/** 后端所有时间均为 UTC（naive，无时区标记），
 * 前端解析时需补上 'Z' 再转本地时间，否则会少 8 小时（中国时区）。 */

/** 将后端时间字符串解析为 Date；无时区标记的按 UTC 处理 */
export function toDate(s) {
  if (!s) return null
  const t = typeof s === 'string' && !/[zZ]|[+-]\d{2}:?\d{2}$/.test(s) ? `${s}Z` : s
  const d = new Date(t)
  return isNaN(d.getTime()) ? null : d
}

/** 完整时间：yyyy/M/d HH:mm:ss（本地时区） */
export function fmtTime(s) {
  const d = toDate(s)
  return d ? d.toLocaleString('zh-CN', { hour12: false }) : '-'
}
