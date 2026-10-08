// Usage: node scripts/capture.mjs <url> <outPrefix>  — full-page screenshots (desktop+mobile) and computed styles of main blocks.
import { chromium } from 'playwright'
import { writeFileSync } from 'node:fs'

const [url, out] = process.argv.slice(2)
const browser = await chromium.launch({ channel: 'chrome' })
const styles = {}
for (const [name, vp] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
  const page = await browser.newPage({ viewport: vp })
  for (let i = 0; ; i++) {
    try { await page.goto(url, { waitUntil: 'load', timeout: 60000 }); break } catch (e) { if (i >= 3) throw e; await page.waitForTimeout(2000) }
  }
  await page.waitForTimeout(2500)
  await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 120)) } window.scrollTo(0, 0) })
  await page.screenshot({ path: `${out}-${name}.png`, fullPage: true })
  if (name === 'desktop') {
    styles.blocks = await page.evaluate(() => {
      const pick = (el) => { const c = getComputedStyle(el), r = el.getBoundingClientRect(); return { tag: el.tagName.toLowerCase(), cls: String(el.className).slice(0, 60), x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height), color: c.color, bg: c.backgroundColor, bgImage: c.backgroundImage.slice(0, 80), font: `${c.fontWeight} ${c.fontSize}/${c.lineHeight} ${c.fontFamily.split(',')[0]}`, pad: c.padding, radius: c.borderRadius } }
      const sels = ['body', 'header', 'nav', 'main', 'h1', 'h2', 'h3', 'p', 'a', '.wp-block-cover', '.wp-block-columns', '.wp-block-column', '.wp-block-button__link', '.wp-block-group', '.alianzas-carousel-item', 'footer']
      return Object.fromEntries(sels.map((s) => [s, [...document.querySelectorAll(s)].slice(0, 3).map(pick)]))
    })
  }
  await page.close()
}
writeFileSync(`${out}-styles.json`, JSON.stringify(styles, null, 1))
await browser.close()
console.log('done')
