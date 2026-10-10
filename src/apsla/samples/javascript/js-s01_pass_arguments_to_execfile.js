import { execFile } from "node:child_process";
execFile("ls", ["-l", dir], callback);
