import puppeteer, { Browser, Page } from "puppeteer";

let browser: Browser | undefined;
let page: Page | undefined;

async function getPage(): Promise<Page> {
  if (!browser) {
    browser = await puppeteer.launch({ headless: true });
  }
  if (!page || page.isClosed()) {
    page = await browser.newPage();
  }
  return page;
}

export async function openUrl(url: string): Promise<{ title: string; url: string }> {
  const p = await getPage();
  await p.goto(url, { waitUntil: "domcontentloaded" });
  return { title: await p.title(), url: p.url() };
}

export async function getPageText(): Promise<string> {
  const p = await getPage();
  return p.evaluate(() => document.body?.innerText ?? "");
}

export async function screenshot(): Promise<string> {
  const p = await getPage();
  const base64 = await p.screenshot({ encoding: "base64", type: "png" });
  return base64 as string;
}

export async function closeBrowser(): Promise<void> {
  await browser?.close();
  browser = undefined;
  page = undefined;
}
