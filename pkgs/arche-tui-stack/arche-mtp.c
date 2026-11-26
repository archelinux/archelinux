/* SPDX-License-Identifier: GPL-3.0-only */
#define _POSIX_C_SOURCE 200809L

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <libmtp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static void usage(FILE *stream)
{
    fputs("Usage: arche-mtp shell\n"
          "       arche-mtp ls [FOLDER_ID]\n"
          "       arche-mtp put LOCAL_FILE [FOLDER_ID]\n"
          "       arche-mtp get FILE_ID LOCAL_FILE\n", stream);
}

static int parse_id(const char *text, uint32_t *id)
{
    if (!*text || text[strspn(text, "0123456789")])
        return -1;
    errno = 0;
    uintmax_t value = strtoumax(text, NULL, 10);
    if (errno || !value || value >= UINT32_MAX)
        return -1;
    *id = (uint32_t)value;
    return 0;
}

static LIBMTP_mtpdevice_t *open_device(void)
{
    LIBMTP_Init();
    LIBMTP_raw_device_t *devices = NULL;
    int count = 0;
    LIBMTP_error_number_t status = LIBMTP_Detect_Raw_Devices(&devices, &count);
    LIBMTP_mtpdevice_t *device = NULL;
    if (status == LIBMTP_ERROR_NO_DEVICE_ATTACHED || (!status && !count)) {
        fputs("No MTP device found. Unlock the phone and select File transfer.\n", stderr);
    } else if (status) {
        fprintf(stderr, "MTP detection failed (%d).\n", status);
    } else if (count != 1) {
        fputs("Leave only the phone you want to use connected in File transfer mode.\n", stderr);
    } else {
        /* A cached session can scan the entire phone before the first command. */
        device = LIBMTP_Open_Raw_Device_Uncached(devices);
        if (!device)
            fputs("Could not open the phone. Check USB permissions and close other file transfer apps.\n", stderr);
    }
    free(devices);
    return device;
}

static int list_files(LIBMTP_mtpdevice_t *device, uint32_t folder)
{
    LIBMTP_file_t *entry = LIBMTP_Get_Files_And_Folders(device, 0, folder);
    while (entry) {
        printf("%" PRIu32 "\t%s\t", entry->item_id,
               entry->filetype == LIBMTP_FILETYPE_FOLDER ? "folder" : "file");
        if (entry->filename) {
            for (const unsigned char *c = (const unsigned char *)entry->filename; *c; ++c)
                putchar(*c < 32 || *c == 127 ? '?' : *c);
        }
        putchar('\n');
        LIBMTP_file_t *next = entry->next;
        LIBMTP_destroy_file_t(entry);
        entry = next;
    }
    return LIBMTP_Get_Errorstack(device) ? -1 : 0;
}

static int put_file(LIBMTP_mtpdevice_t *device, const char *path, uint32_t folder)
{
    uint32_t storage = 0;
    if (folder) {
        LIBMTP_file_t *parent = LIBMTP_Get_Filemetadata(device, folder);
        if (!parent || parent->filetype != LIBMTP_FILETYPE_FOLDER) {
            if (parent)
                LIBMTP_destroy_file_t(parent);
            fputs("The destination ID does not identify a folder.\n", stderr);
            return -1;
        }
        storage = parent->storage_id;
        LIBMTP_destroy_file_t(parent);
    } else {
        if (!device->storage) {
            fputs("The phone did not expose any storage. Keep it unlocked.\n", stderr);
            return -1;
        }
        storage = device->storage->id;
    }

    int fd = open(path, O_RDONLY | O_NONBLOCK);
    if (fd < 0) {
        perror(path);
        return -1;
    }
    struct stat st;
    if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode)) {
        fputs("The upload source must be a readable regular file.\n", stderr);
        close(fd);
        return -1;
    }

    const char *base = strrchr(path, '/');
    LIBMTP_file_t *file = LIBMTP_new_file_t();
    if (!file) {
        close(fd);
        return -1;
    }
    file->filename = strdup(base ? base + 1 : path);
    file->parent_id = folder ? folder : LIBMTP_FILES_AND_FOLDERS_ROOT;
    file->storage_id = storage;
    file->filesize = (uint64_t)st.st_size;
    file->filetype = LIBMTP_FILETYPE_UNKNOWN;

    int result = file->filename
        ? LIBMTP_Send_File_From_File_Descriptor(device, fd, file, NULL, NULL) : -1;
    if (!result)
        printf("Uploaded file ID: %" PRIu32 "\n", file->item_id);
    LIBMTP_destroy_file_t(file);
    close(fd);
    return result;
}

static int get_file(LIBMTP_mtpdevice_t *device, uint32_t id, const char *path)
{
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0) {
        perror(path);
        return -1;
    }
    int result = LIBMTP_Get_File_To_File_Descriptor(device, id, fd, NULL, NULL);
    if (close(fd) != 0) {
        perror(path);
        result = -1;
    }
    if (result && unlink(path) != 0)
        perror(path);
    return result;
}

static void report_error(LIBMTP_mtpdevice_t *device)
{
    fputs("MTP operation failed.\n", stderr);
    LIBMTP_Dump_Errorstack(device);
}

static char *skip_space(char *text)
{
    while (isspace((unsigned char)*text))
        ++text;
    return text;
}

static char *next_word(char **rest)
{
    char *word = skip_space(*rest);
    char *end = word;
    while (*end && !isspace((unsigned char)*end))
        ++end;
    if (*end)
        *end++ = '\0';
    *rest = skip_space(end);
    return word;
}

/* Keep the device open between commands. Some Android phones reset USB on close. */
static int interactive(LIBMTP_mtpdevice_t *device)
{
    char *line = NULL;
    size_t capacity = 0;
    uint32_t folder = 0;
    int failed = 0;
    int prompt = isatty(STDIN_FILENO);

    if (prompt)
        puts("Commands: ls, cd [FOLDER_ID], put LOCAL_FILE, get FILE_ID LOCAL_FILE, quit");
    for (;;) {
        if (prompt)
            fputs("mtp> ", stdout);
        fflush(stdout);
        ssize_t length = getline(&line, &capacity, stdin);
        if (length < 0)
            break;
        if (length && line[length - 1] == '\n')
            line[length - 1] = '\0';
        char *args = line;
        char *command = next_word(&args);
        if (!*command)
            continue;
        if (strcmp(command, "quit") == 0 && !*args)
            break;

        LIBMTP_Clear_Errorstack(device);
        int result = 0;
        uint32_t id = 0;
        if (strcmp(command, "ls") == 0 && !*args) {
            result = list_files(device, folder ? folder : LIBMTP_FILES_AND_FOLDERS_ROOT);
        } else if (strcmp(command, "cd") == 0 && (!*args || !parse_id(args, &id))) {
            if (!id) {
                folder = 0;
            } else {
                LIBMTP_file_t *target = LIBMTP_Get_Filemetadata(device, id);
                if (target && target->filetype == LIBMTP_FILETYPE_FOLDER)
                    folder = id;
                else {
                    fputs("The destination ID does not identify a folder.\n", stderr);
                    result = -1;
                }
                if (target)
                    LIBMTP_destroy_file_t(target);
            }
        } else if (strcmp(command, "put") == 0 && *args) {
            result = put_file(device, args, folder);
        } else if (strcmp(command, "get") == 0 && !parse_id(next_word(&args), &id) && *args) {
            result = get_file(device, id, args);
        } else {
            fputs("Commands: ls, cd [FOLDER_ID], put LOCAL_FILE, get FILE_ID LOCAL_FILE, quit\n", stderr);
            result = -1;
        }
        if (result) {
            report_error(device);
            failed = 1;
        }
    }
    free(line);
    return failed || ferror(stdin) ? -1 : 0;
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        usage(stdout);
        return 0;
    }

    enum { LIST, PUT, GET, SHELL } operation;
    uint32_t id = 0;
    if (argc == 2 && strcmp(argv[1], "shell") == 0) {
        operation = SHELL;
    } else if ((argc == 2 || argc == 3) && strcmp(argv[1], "ls") == 0) {
        operation = LIST;
        id = LIBMTP_FILES_AND_FOLDERS_ROOT;
        if (argc == 3 && parse_id(argv[2], &id))
            goto invalid;
    } else if ((argc == 3 || argc == 4) && strcmp(argv[1], "put") == 0) {
        operation = PUT;
        if (argc == 4 && parse_id(argv[3], &id))
            goto invalid;
    } else if (argc == 4 && strcmp(argv[1], "get") == 0 && !parse_id(argv[2], &id)) {
        operation = GET;
    } else {
        goto invalid;
    }

    LIBMTP_mtpdevice_t *device = open_device();
    if (!device)
        return 1;

    LIBMTP_Clear_Errorstack(device);
    int result = -1;
    switch (operation) {
    case LIST: result = list_files(device, id); break;
    case PUT: result = put_file(device, argv[2], id); break;
    case GET: result = get_file(device, id, argv[3]); break;
    case SHELL: result = interactive(device); break;
    }
    if (result && operation != SHELL)
        report_error(device);
    LIBMTP_Release_Device(device);
    return result ? 1 : 0;

invalid:
    usage(stderr);
    return 2;
}
