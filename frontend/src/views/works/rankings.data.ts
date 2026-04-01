import type { WorkPieceRankingItem, WorkRankingItem } from '@/api/works'

export type RankingBoardKey = 'works' | 'users' | 'dailyWord'
export type RankingPeriodValue = 'all' | 'monthly' | 'weekly' | 'daily'
export type WorkRankingTypeValue = 'composite' | 'ai_score' | 'popularity'

export interface DailyWordRankingItem {
  rank: number
  word_id: number
  word: string
  pinyin: string
  category: string
  description: string
  heat_score: number
  usage_count: number
  creator_count: number
  sample_title: string
}

interface MockWorkSeed extends Omit<WorkPieceRankingItem, 'rank' | 'composite_score'> {}

interface MockUserSeed {
  user_id: number
  username: string
  avatar_url: string | null
  exp: number
  level: number
  metrics: Record<'all' | 'weekly' | 'daily', {
    work_count: number
    total_likes: number
    avg_score: number | null
  }>
}

interface MockDailyWordSeed {
  word_id: number
  word: string
  pinyin: string
  category: string
  description: string
  sample_title: string
  metrics: Record<'all' | 'weekly' | 'daily', {
    heat_score: number
    usage_count: number
    creator_count: number
  }>
}

const now = Date.now()
const dayMs = 24 * 60 * 60 * 1000

function toIso(daysAgo: number, hoursAgo = 0) {
  return new Date(now - daysAgo * dayMs - hoursAgo * 60 * 60 * 1000).toISOString()
}

function computeCompositeScore(likeCount: number, aiTotalScore: number | null, viewCount: number) {
  const likeScore = Math.min(likeCount * 2, 100)
  const aiScore = aiTotalScore ?? 0
  const viewScore = Math.min(viewCount * 0.1, 20)
  return Number((aiScore * 0.5 + likeScore * 0.35 + viewScore * 0.15).toFixed(2))
}

function matchesPeriod(dateValue: string | null, period: RankingPeriodValue) {
  if (!dateValue || period === 'all') {
    return true
  }

  const diff = now - new Date(dateValue).getTime()

  if (period === 'daily') {
    return diff <= dayMs
  }

  if (period === 'weekly') {
    return diff <= dayMs * 7
  }

  if (period === 'monthly') {
    return diff <= dayMs * 30
  }

  return true
}

function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize
  return items.slice(start, start + pageSize)
}

function rankItems<T>(items: T[]) {
  return items.map((item, index) => ({
    ...item,
    rank: index + 1
  }))
}

function normalizeMockPeriod(period: RankingPeriodValue): 'all' | 'weekly' | 'daily' {
  if (period === 'daily' || period === 'weekly' || period === 'all') {
    return period
  }

  return 'all'
}

const mockWorkSeeds: MockWorkSeed[] = [
  {
    work_id: 101,
    title: '花香蝶影_春信',
    content: '春山入墨迟\n溪月照松枝\n纸上新词暖\n清风与我知',
    genre: '七言绝句',
    user_id: 21,
    username: '沈砚秋',
    avatar_url: null,
    like_count: 126,
    view_count: 538,
    ai_grammar_score: 94,
    ai_artistic_score: 92,
    ai_total_score: 93,
    published_at: toIso(0, 6)
  },
  {
    work_id: 102,
    title: '竹韵松风_月魂',
    content: '雨洗青苔净\n云分竹影深\n小窗临古帖\n一字见初心',
    genre: '五言律诗',
    user_id: 22,
    username: '顾清和',
    avatar_url: null,
    like_count: 98,
    view_count: 412,
    ai_grammar_score: 90,
    ai_artistic_score: 89,
    ai_total_score: 90,
    published_at: toIso(2, 3)
  },
  {
    work_id: 103,
    title: '云水禅心_墨痕',
    content: '水纹轻皱月华新\n小桨归时岸柳匀\n一段清辞留白处\n更添江上晚来春',
    genre: '词',
    user_id: 23,
    username: '柳知微',
    avatar_url: null,
    like_count: 118,
    view_count: 620,
    ai_grammar_score: 88,
    ai_artistic_score: 95,
    ai_total_score: 91,
    published_at: toIso(5, 8)
  },
  {
    work_id: 104,
    title: '灯火阑珊_夜读',
    content: '灯静书声慢\n更深砚气温\n一行唐句在\n照见读诗人',
    genre: '五言绝句',
    user_id: 24,
    username: '陆行川',
    avatar_url: null,
    like_count: 76,
    view_count: 301,
    ai_grammar_score: 86,
    ai_artistic_score: 87,
    ai_total_score: 86,
    published_at: toIso(8, 10)
  },
  {
    work_id: 105,
    title: '芦花渡口_新声',
    content: '蘸水芦花白\n鸣榔夜色分\n归舟摇一盏\n照破渡头云',
    genre: '七言律诗',
    user_id: 25,
    username: '温如岚',
    avatar_url: null,
    like_count: 132,
    view_count: 690,
    ai_grammar_score: 91,
    ai_artistic_score: 93,
    ai_total_score: 92,
    published_at: toIso(12, 4)
  },
  {
    work_id: 106,
    title: '秋声入句_霜笔',
    content: '一叶先知晚\n疏钟入短窗\n新凉辞未稳\n已觉笔端霜',
    genre: '七言绝句',
    user_id: 26,
    username: '白临舟',
    avatar_url: null,
    like_count: 64,
    view_count: 256,
    ai_grammar_score: 83,
    ai_artistic_score: 84,
    ai_total_score: 84,
    published_at: toIso(16, 7)
  },
  {
    work_id: 107,
    title: '潮生海色_乡书',
    content: '潮痕初上石\n海色半侵窗\n欲写乡关远\n先闻雁一双',
    genre: '自由体',
    user_id: 27,
    username: '周星阑',
    avatar_url: null,
    like_count: 88,
    view_count: 470,
    ai_grammar_score: null,
    ai_artistic_score: null,
    ai_total_score: null,
    published_at: toIso(23, 5)
  },
  {
    work_id: 108,
    title: '竹里清风_茶烟',
    content: '对坐无人处\n风声替我言\n茶烟分远近\n皆入一窗山',
    genre: '五言绝句',
    user_id: 28,
    username: '许见山',
    avatar_url: null,
    like_count: 58,
    view_count: 220,
    ai_grammar_score: 81,
    ai_artistic_score: 82,
    ai_total_score: 81,
    published_at: toIso(34, 2)
  }
]

const mockUserSeeds: MockUserSeed[] = [
  {
    user_id: 21,
    username: '沈砚秋',
    avatar_url: null,
    exp: 1680,
    level: 6,
    metrics: {
      all: { work_count: 18, total_likes: 468, avg_score: 91.6 },
      weekly: { work_count: 4, total_likes: 116, avg_score: 92.3 },
      daily: { work_count: 1, total_likes: 38, avg_score: 93.0 }
    }
  },
  {
    user_id: 22,
    username: '顾清和',
    avatar_url: null,
    exp: 1120,
    level: 5,
    metrics: {
      all: { work_count: 16, total_likes: 421, avg_score: 90.4 },
      weekly: { work_count: 3, total_likes: 96, avg_score: 91.2 },
      daily: { work_count: 1, total_likes: 24, avg_score: 90.0 }
    }
  },
  {
    user_id: 23,
    username: '柳知微',
    avatar_url: null,
    exp: 2360,
    level: 7,
    metrics: {
      all: { work_count: 15, total_likes: 408, avg_score: 91.1 },
      weekly: { work_count: 4, total_likes: 102, avg_score: 91.8 },
      daily: { work_count: 1, total_likes: 22, avg_score: 91.0 }
    }
  },
  {
    user_id: 24,
    username: '陆行川',
    avatar_url: null,
    exp: 640,
    level: 4,
    metrics: {
      all: { work_count: 13, total_likes: 352, avg_score: 88.7 },
      weekly: { work_count: 2, total_likes: 74, avg_score: 89.5 },
      daily: { work_count: 1, total_likes: 19, avg_score: 88.0 }
    }
  },
  {
    user_id: 25,
    username: '温如岚',
    avatar_url: null,
    exp: 3180,
    level: 8,
    metrics: {
      all: { work_count: 19, total_likes: 516, avg_score: 92.1 },
      weekly: { work_count: 4, total_likes: 132, avg_score: 92.8 },
      daily: { work_count: 1, total_likes: 35, avg_score: 92.0 }
    }
  },
  {
    user_id: 26,
    username: '白临舟',
    avatar_url: null,
    exp: 360,
    level: 3,
    metrics: {
      all: { work_count: 12, total_likes: 298, avg_score: 87.9 },
      weekly: { work_count: 3, total_likes: 68, avg_score: 88.2 },
      daily: { work_count: 1, total_likes: 17, avg_score: 84.0 }
    }
  }
]

const mockDailyWordSeeds: MockDailyWordSeed[] = [
  {
    word_id: 301,
    word: '春',
    pinyin: 'chūn',
    category: '时令意象',
    description: '在作品里最常被用于起笔与转情，常与山水、花影并置。',
    sample_title: '花香蝶影_春信',
    metrics: {
      all: { heat_score: 98, usage_count: 186, creator_count: 72 },
      weekly: { heat_score: 94, usage_count: 54, creator_count: 28 },
      daily: { heat_score: 91, usage_count: 16, creator_count: 9 }
    }
  },
  {
    word_id: 302,
    word: '月',
    pinyin: 'yuè',
    category: '清景意象',
    description: '常用于营造静夜氛围，也是抒怀与寄远最稳定的核心词。',
    sample_title: '云水禅心_墨痕',
    metrics: {
      all: { heat_score: 96, usage_count: 171, creator_count: 68 },
      weekly: { heat_score: 92, usage_count: 47, creator_count: 24 },
      daily: { heat_score: 87, usage_count: 12, creator_count: 7 }
    }
  },
  {
    word_id: 303,
    word: '山',
    pinyin: 'shān',
    category: '空间意象',
    description: '多用于形成纵深感，适合放在句尾收束画面与气口。',
    sample_title: '竹里清风_茶烟',
    metrics: {
      all: { heat_score: 90, usage_count: 146, creator_count: 59 },
      weekly: { heat_score: 84, usage_count: 38, creator_count: 19 },
      daily: { heat_score: 78, usage_count: 10, creator_count: 5 }
    }
  },
  {
    word_id: 304,
    word: '雨',
    pinyin: 'yǔ',
    category: '动态景物',
    description: '适合承接窗、灯、夜等细部场景，能快速建立听觉层次。',
    sample_title: '竹韵松风_月魂',
    metrics: {
      all: { heat_score: 88, usage_count: 133, creator_count: 53 },
      weekly: { heat_score: 83, usage_count: 35, creator_count: 18 },
      daily: { heat_score: 80, usage_count: 11, creator_count: 6 }
    }
  },
  {
    word_id: 305,
    word: '风',
    pinyin: 'fēng',
    category: '流动意象',
    description: '常与声、影、香等感官词联动，是提升句面流动感的高频词。',
    sample_title: '芦花渡口_新声',
    metrics: {
      all: { heat_score: 86, usage_count: 128, creator_count: 49 },
      weekly: { heat_score: 82, usage_count: 31, creator_count: 16 },
      daily: { heat_score: 77, usage_count: 9, creator_count: 5 }
    }
  },
  {
    word_id: 306,
    word: '梦',
    pinyin: 'mèng',
    category: '情感转折',
    description: '适合承接回忆与虚境，是构建层次与留白感的常见入口。',
    sample_title: '潮生海色_乡书',
    metrics: {
      all: { heat_score: 84, usage_count: 117, creator_count: 46 },
      weekly: { heat_score: 79, usage_count: 28, creator_count: 14 },
      daily: { heat_score: 73, usage_count: 8, creator_count: 4 }
    }
  }
]

export function getMockWorkRankingResponse(options: {
  rankingType: WorkRankingTypeValue
  period: RankingPeriodValue
  genre?: string
  page: number
  pageSize: number
}) {
  const filtered = mockWorkSeeds
    .filter((item) => !options.genre || item.genre === options.genre)
    .filter((item) => matchesPeriod(item.published_at, options.period))
    .map((item) => ({
      ...item,
      composite_score: computeCompositeScore(item.like_count, item.ai_total_score, item.view_count)
    }))

  const sorted = filtered.sort((a, b) => {
    if (options.rankingType === 'ai_score') {
      return (b.ai_total_score ?? 0) - (a.ai_total_score ?? 0) || b.like_count - a.like_count
    }

    if (options.rankingType === 'popularity') {
      return b.like_count - a.like_count || b.view_count - a.view_count
    }

    return b.composite_score - a.composite_score || b.like_count - a.like_count
  })

  const ranked = rankItems(sorted)

  return {
    items: paginate(ranked, options.page, options.pageSize),
    total: ranked.length
  }
}

export function getMockUserRankingResponse(options: {
  period: RankingPeriodValue
  page: number
  pageSize: number
}) {
  const normalizedPeriod = normalizeMockPeriod(options.period)
  const ranked = rankItems(
    mockUserSeeds
      .map<WorkRankingItem>((item) => ({
        rank: 0,
        user_id: item.user_id,
        username: item.username,
        avatar_url: item.avatar_url,
        exp: item.exp,
        level: item.level,
        work_count: item.metrics[normalizedPeriod].work_count,
        total_likes: item.metrics[normalizedPeriod].total_likes,
        avg_score: item.metrics[normalizedPeriod].avg_score
      }))
      .sort((a, b) => b.total_likes - a.total_likes || (b.avg_score ?? 0) - (a.avg_score ?? 0))
    )

  return {
    items: paginate(ranked, options.page, options.pageSize),
    total: ranked.length
  }
}

export function getMockDailyWordRankingResponse(options: {
  period: RankingPeriodValue
  page: number
  pageSize: number
}) {
  const normalizedPeriod = normalizeMockPeriod(options.period)
  const ranked = rankItems(
    mockDailyWordSeeds
      .map<DailyWordRankingItem>((item) => ({
        rank: 0,
        word_id: item.word_id,
        word: item.word,
        pinyin: item.pinyin,
        category: item.category,
        description: item.description,
        heat_score: item.metrics[normalizedPeriod].heat_score,
        usage_count: item.metrics[normalizedPeriod].usage_count,
        creator_count: item.metrics[normalizedPeriod].creator_count,
        sample_title: item.sample_title
      }))
      .sort((a, b) => b.heat_score - a.heat_score || b.usage_count - a.usage_count)
  )

  return {
    items: paginate(ranked, options.page, options.pageSize),
    total: ranked.length
  }
}
