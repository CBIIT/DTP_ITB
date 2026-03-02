import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

/**
 * GET /api/pdf?name=<report_name>
 *
 * Serves a PDF file from the directory specified by the PDF_DIRECTORY
 * environment variable. The PDF filename is derived from the report name
 * by replacing the file extension with `.pdf`.
 */
export async function GET(request: NextRequest) {
  const name = request.nextUrl.searchParams.get("name");
  if (!name) {
    return NextResponse.json(
      { error: "Missing 'name' query parameter" },
      { status: 400 },
    );
  }

  const pdfDir = process.env.PDF_DIRECTORY;
  if (!pdfDir) {
    return NextResponse.json(
      { error: "PDF_DIRECTORY environment variable is not configured" },
      { status: 500 },
    );
  }

  // Derive the PDF filename: replace file extension with .pdf
  const baseName = name.replace(/\.[^.]+$/, "");
  const pdfFileName = `${baseName}.pdf`;

  // Resolve and validate the path to prevent directory traversal
  const resolvedDir = path.resolve(pdfDir);
  const filePath = path.join(resolvedDir, pdfFileName);
  if (!filePath.startsWith(resolvedDir + path.sep)) {
    return NextResponse.json({ error: "Invalid file name" }, { status: 400 });
  }

  if (!fs.existsSync(filePath)) {
    return NextResponse.json(
      { error: `PDF not found: ${pdfFileName}` },
      { status: 404 },
    );
  }

  const fileBuffer = await fs.promises.readFile(filePath);
  return new NextResponse(fileBuffer, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `inline; filename="${pdfFileName}"`,
    },
  });
}
