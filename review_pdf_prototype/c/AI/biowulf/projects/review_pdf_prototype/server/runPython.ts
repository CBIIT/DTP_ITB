import { execFile } from "child_process";

/** Use `python` on Windows and `python3` everywhere else. */
const PYTHON =
  process.env.PYTHON_PATH ?? (process.platform === "win32" ? "python" : "python3");

/**
 * Execute a Python script and return its stdout output.
 *
 * @param scriptPath - Absolute path to the Python script.
 * @param args       - Optional command-line arguments.
 * @returns The script's stdout as a string.
 */
export function runPython(
  scriptPath: string,
  args: string[] = [],
): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      PYTHON,
      [scriptPath, ...args],
      {
        env: { ...process.env },
        timeout: 30_000,
      },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(stderr || error.message));
        } else {
          resolve(stdout);
        }
      },
    );
  });
}
