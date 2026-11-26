(comment) @comment
(interpreted_string_literal) @string
(raw_string_literal) @string
(rune_literal) @character
(int_literal) @number
(float_literal) @number.float
(function_declaration name: (identifier) @function)
(method_declaration name: (field_identifier) @function.method)
(type_identifier) @type
["break" "case" "chan" "const" "continue" "default" "defer" "else" "fallthrough"
 "for" "func" "go" "goto" "if" "import" "interface" "map" "package" "range" "return"
 "select" "struct" "switch" "type" "var"] @keyword
