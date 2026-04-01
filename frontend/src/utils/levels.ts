import tongshengIcon from '@/assets/icons/ranks/tongsheng.svg'
import xiucaiIcon from '@/assets/icons/ranks/xiucai.svg'
import jurenIcon from '@/assets/icons/ranks/juren.svg'
import gongshiIcon from '@/assets/icons/ranks/gongshi.svg'
import jinshiIcon from '@/assets/icons/ranks/jinshi.svg'
import tanhuaIcon from '@/assets/icons/ranks/tanhua.svg'
import bangyanIcon from '@/assets/icons/ranks/bangyan.svg'
import zhuangyuanIcon from '@/assets/icons/ranks/zhuangyuan.svg'

export interface RankInfo {
  level: number
  name: string
  key: string
  expRequired: number
  desc: string
  icon: string
  color: string
}

export const RANK_CONFIG: RankInfo[] = [
  { level: 1, name: '童生', key: 'tongsheng', expRequired: 0, desc: '初入诗门，蒙学启智', icon: tongshengIcon, color: '#8b7355' },
  { level: 2, name: '秀才', key: 'xiucai', expRequired: 100, desc: '通晓诗文，小有所成', icon: xiucaiIcon, color: '#5a8a6e' },
  { level: 3, name: '举人', key: 'juren', expRequired: 400, desc: '乡试及第，学贯古今', icon: jurenIcon, color: '#6b5b3e' },
  { level: 4, name: '贡士', key: 'gongshi', expRequired: 800, desc: '会试中式，才华出众', icon: gongshiIcon, color: '#7a6840' },
  { level: 5, name: '进士', key: 'jinshi', expRequired: 1500, desc: '殿试入围，博古通今', icon: jinshiIcon, color: '#b28d57' },
  { level: 6, name: '探花', key: 'tanhua', expRequired: 2500, desc: '金榜题名，才情卓绝', icon: tanhuaIcon, color: '#c4785a' },
  { level: 7, name: '榜眼', key: 'bangyan', expRequired: 4400, desc: '名列前茅，学富五车', icon: bangyanIcon, color: '#8b6914' },
  { level: 8, name: '状元', key: 'zhuangyuan', expRequired: 6000, desc: '独占鳌头，天下无双', icon: zhuangyuanIcon, color: '#c41a1a' },
]

const DEFAULT_RANK = RANK_CONFIG[0] as RankInfo

export function getRankByLevel(level: number): RankInfo {
  const clamped = Math.max(1, Math.min(level, RANK_CONFIG.length))
  return RANK_CONFIG[clamped - 1] ?? DEFAULT_RANK
}

export function getRankByExp(exp: number): RankInfo {
  let result: RankInfo = DEFAULT_RANK
  for (const rank of RANK_CONFIG) {
    if (exp >= rank.expRequired) {
      result = rank
    } else {
      break
    }
  }
  return result
}

export function getNextRank(level: number): RankInfo | null {
  if (level >= RANK_CONFIG.length) return null
  return RANK_CONFIG[level] ?? null
}

export function getExpProgress(exp: number): { current: number; total: number; percent: number } {
  const rank = getRankByExp(exp)
  const next = getNextRank(rank.level)
  if (!next) {
    return { current: exp - rank.expRequired, total: 1, percent: 100 }
  }
  const current = exp - rank.expRequired
  const total = next.expRequired - rank.expRequired
  return { current, total, percent: Math.round((current / total) * 100) }
}
