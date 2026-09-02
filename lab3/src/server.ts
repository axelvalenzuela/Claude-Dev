import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { openUrl, getPageText, screenshot, closeBrowser } from "./tools/browser.js";

const server = new McpServer({
  name: "lab3-mcp-browser",
  version: "1.0.0",
});

server.tool(
  "open_url",
  "Abre una URL en Chromium (headless) y devuelve el titulo y la URL final tras redirecciones",
  { url: z.string().url().describe("URL a abrir, con protocolo (https://...)") },
  async ({ url }) => {
    const result = await openUrl(url);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "get_page_text",
  "Devuelve el texto visible de la pagina actualmente abierta (requiere haber llamado open_url antes)",
  {},
  async () => {
    const text = await getPageText();
    return { content: [{ type: "text", text }] };
  }
);

server.tool(
  "screenshot",
  "Toma una captura de pantalla (PNG) de la pagina actualmente abierta",
  {},
  async () => {
    const base64 = await screenshot();
    return { content: [{ type: "image", data: base64, mimeType: "image/png" }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

process.on("SIGINT", async () => {
  await closeBrowser();
  process.exit(0);
});

main().catch((err) => {
  console.error("Fatal error starting lab3-mcp-browser:", err);
  process.exit(1);
});
