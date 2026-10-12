const generic: Record<string, string> = {
  KEYWORD: 'A reserved word with a meaning defined by the language.',
  IDENTIFIER: 'A name used to refer to a variable, function, type, or other program element.',
  OPERATOR: 'A symbol that performs an operation or connects expressions.',
  DELIMITER: 'A punctuation mark that separates or groups parts of the program.',
  NUMBER_LITERAL: 'A number written directly in the source code.',
  STRING_LITERAL: 'Text written directly in the source code between quote marks.',
  CHAR_LITERAL: 'A character written directly in the source code between quote marks.',
  F_STRING: 'A string that can include values or expressions when the language evaluates it.',
  REGEX_LITERAL: 'A pattern written directly in the source code for matching text.',
  TEMPLATE_LITERAL: 'A template string that can include expressions or interpolated values.',
  PREPROCESSOR: 'A directive handled before the compiler processes the rest of the source.',
  HEADER_NAME: 'A header name used by an include directive.',
  COMMENT: 'A note for readers that the language does not execute as program logic.',
  INVALID_TOKEN: 'Text the lexer could not accept as a valid token for this language.',
  TEXT_BLOCK: 'A multi-line string value written directly in the source code.',
  ANNOTATION: 'A language-specific annotation that provides metadata to tools or the runtime.',
};

const languageNames: Record<string, string> = {
  cpp: 'C++', c: 'C', python: 'Python', java: 'Java', javascript: 'JavaScript',
};

export function explainToken(tokenType: string, language: string): string {
  const explanation = generic[tokenType.toUpperCase()];
  if (!explanation) return `A ${languageNames[language.toLowerCase()] ?? language} language-specific token.`;
  return explanation;
}
