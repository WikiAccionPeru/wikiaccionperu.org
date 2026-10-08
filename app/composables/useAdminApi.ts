/** Fetch wrapper for the /api/admin/* endpoints: returns data or throws a human message. */
export const adminError = (e: any): string => e?.data?.statusMessage || e?.statusMessage || e?.message || 'Error'
export const adminFetch = async <T>(url: string, opts: Parameters<typeof $fetch>[1] = {}): Promise<T> => {
  try { return (await $fetch(url, opts as any)) as T } catch (e) { throw new Error(adminError(e)) }
}
