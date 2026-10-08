// Runs before dev/build/install: a fresh `git clone` has the committed sample but none of the generated data files.
// Copies the pruned seed copies into data/ when missing, so the sample site starts without any WordPress access.
import { copyFileSync, existsSync, mkdirSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const seed = join(here, 'seed-data')
const data = join(here, '..', '..', 'data')
mkdirSync(data, { recursive: true })
for (const f of readdirSync(seed)) {
  if (f.endsWith('.json') && !existsSync(join(data, f))) { copyFileSync(join(seed, f), join(data, f)); console.log(`[wp] seeded data/${f}`) }
}
