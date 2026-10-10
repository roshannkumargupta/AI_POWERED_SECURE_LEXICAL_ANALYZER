package demo;
import java.util.*;
@interface Mark { String value(); }
record Item<T>(T value) {}
class LexerShowcase {
  String text = "quotes \" and // not comment";
  long count = 1_000L + 0x1F + 0b101;
  float ratio = 1e3f;
  java.util.function.Function<String, String> fn = value -> switch (value) { case "x" -> "/* text */"; default -> "ok"; };
  String block = """
    text block
    """;
}
