# S-1: Verified Sample Catalogue

## Plain-English overview

SecureLex now gets demonstration samples from a manifest-backed catalogue. Each entry ties a readable source file to metadata describing its language, category, expected findings, Unicode code points, and demo order. The loader validates the manifest and reads sources as UTF-8. The existing sample API fields remain available so the IDE can still open its original presets.

The verification script runs the actual analyzer on each shipped sample. It checks finding IDs and locations, clean examples, taint traces, fix verification, analysis time, and generated special characters. The current engine does not track tainted input through a helper function parameter into `os.system`, so that example remains in `pending/` and is not exposed by the API.

## Glossary

- **Manifest:** JSON catalogue describing sample files and expected behavior.
- **Taint:** Data-flow tracking from untrusted input to a sensitive operation.
- **Pending sample:** A sample withheld from the API because current analyzer behavior does not meet its documented expectation.
- **Unicode code point:** A numbered character value such as U+202E.
- **Idempotent build:** Re-running the generator produces the same sample files and manifest.

## Viva questions

1. **Why keep sample metadata separate from source code?**  
   The manifest can describe demo order, expected rules, language, and special characters while source files stay readable and independently analyzable.

2. **How does the sample loader find files after packaging?**  
   It uses `importlib.resources`, which reads files associated with the installed `apsla.samples` package.

3. **Why are Unicode samples generated?**  
   Editors and copy/paste can alter invisible or directional characters. The builder inserts explicit code points deterministically and records them in metadata.

4. **When should a sample be marked pending?**  
   After checking its source and confirming the current engine misses a required finding or behavior. The manifest records the reason and the loader keeps it out of the API.

5. **How does the new API preserve the old IDE behavior?**  
   Existing sample IDs and fields, including `code`, remain in the default response. New metadata and a metadata-only query are additive.
