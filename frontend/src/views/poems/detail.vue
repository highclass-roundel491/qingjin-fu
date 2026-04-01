<template>
  <div class="detail-page">
    <div class="detail-ink-float"></div>
    <div class="detail-ink-float-2"></div>

    <nav class="detail-nav" :class="{ scrolled: isScrolled }">
      <div class="detail-nav-inner">
        <div class="detail-nav-left">
          <button class="detail-back-btn" @click="goBack">
            <span class="detail-back-arrow">←</span>
            <span>返回</span>
          </button>
          <span class="detail-nav-title">{{ poem?.title }}</span>
        </div>
        <div class="detail-nav-actions">
          <button
            v-if="userStore.isLogin"
            class="fav-btn"
            :class="{ favorited: isFavorited }"
            @click="toggleFavorite"
          >
            <span class="fav-icon">{{ isFavorited ? '藏' : '收' }}</span>
            <span>{{ isFavorited ? '已收藏' : '收藏' }}</span>
          </button>
        </div>
      </div>
    </nav>

    <div class="detail-content">
      <div v-if="loading" class="detail-loading">
        <div class="detail-loading-spinner"></div>
        <span class="detail-loading-text">正在加载...</span>
      </div>

      <template v-else-if="poem">
        <div class="detail-body">
          <div class="detail-main">
            <div class="poem-hero">
              <span class="poem-dynasty-badge">{{ poem.dynasty }}</span>
              <h1 class="poem-main-title">{{ poem.title }}</h1>
              <div class="poem-author-info">
                <span class="poem-author-name">〔{{ poem.dynasty }}〕{{ poem.author }}</span>
              </div>
              <div class="poem-meta">
                <span class="poem-meta-item" v-if="poem.genre">
                  <span class="poem-meta-item__mark">体</span>
                  {{ poem.genre }}
                </span>
                <span class="poem-meta-item" v-if="poem.category">
                  <span class="poem-meta-item__mark">题</span>
                  {{ poem.category }}
                </span>
                <span class="poem-meta-item">
                  <span class="poem-meta-item__mark">阅</span>
                  {{ poem.view_count }}
                </span>
                <span class="poem-meta-item">
                  <span class="poem-meta-item__mark">藏</span>
                  {{ poem.favorite_count }}
                </span>
              </div>
            </div>

            <div class="poem-divider">
              <span class="divider-line"></span>
              <span class="divider-dot"></span>
              <span class="divider-line"></span>
            </div>

            <div class="poem-body">
              <div class="poem-body-corner corner-tl"></div>
              <div class="poem-body-corner corner-tr"></div>
              <div class="poem-body-corner corner-bl"></div>
              <div class="poem-body-corner corner-br"></div>
              <div class="poem-body-seal">赋</div>
              <div class="poem-lines">
                <div
                  v-for="(line, index) in poemLines"
                  :key="index"
                  class="poem-line"
                  :style="{ animationDelay: `${0.3 + index * 0.1}s` }"
                >{{ line }}</div>
              </div>
            </div>

            <section class="study-panel">
              <div class="study-panel__summary">
                <p class="study-panel__eyebrow">READING GUIDE</p>
                <h2 class="study-panel__title">读法提要</h2>
                <p class="study-panel__text">{{ studyGuideText }}</p>
              </div>

              <div class="study-facts">
                <article v-for="fact in quickFacts" :key="fact.label" class="study-fact">
                  <span class="study-fact__label">{{ fact.label }}</span>
                  <strong class="study-fact__value">{{ fact.value }}</strong>
                </article>
              </div>

              <div class="study-actions">
                <button
                  v-if="userStore.isLogin"
                  type="button"
                  class="study-action study-action--primary"
                  @click="toggleFavorite"
                >
                  <span class="study-action__mark">{{ isFavorited ? '藏' : '收' }}</span>
                  <span>{{ isFavorited ? '已收入卷柜' : '收入卷柜' }}</span>
                </button>
                <button type="button" class="study-action" @click="openRandomPoem" :disabled="loadingRandom">
                  <span class="study-action__mark">换</span>
                  <span>{{ loadingRandom ? '寻卷中' : '再读一卷' }}</span>
                </button>
              </div>
            </section>

          </div>

          <aside class="detail-aside-left">
            <section v-if="availableTabs.length" class="aside-card aside-card--tabs">
              <div class="tabs-header">
                <button
                  v-for="tab in availableTabs"
                  :key="tab.key"
                  class="tab-btn"
                  :class="{ active: activeTab === tab.key }"
                  @click="activeTab = tab.key"
                >{{ tab.label }}</button>
              </div>
              <div class="tab-content">
                <template v-if="activeTab === 'poet'">
                  <div v-if="poetInfo" class="poet-profile">
                    <div class="poet-profile__name-row">
                      <span class="poet-profile__name">{{ poetInfo.name }}</span>
                      <span v-if="poetInfo.alias" class="poet-profile__alias">{{ poetInfo.alias }}</span>
                      <span class="aside-card__badge">{{ poetInfo.dynasty }}</span>
                    </div>
                    <p v-if="poetInfo.birth_death_desc" class="poet-profile__years">{{ poetInfo.birth_death_desc }}</p>
                    <div v-if="poetInfo.styles" class="poet-profile__styles">
                      <span v-for="s in poetInfo.styles.split('、')" :key="s" class="poet-profile__style-tag">{{ s }}</span>
                    </div>
                    <p v-if="poetInfo.brief" class="poet-profile__brief">{{ poetInfo.brief }}</p>
                    <div v-if="poetInfo.representative_works" class="poet-profile__works">
                      <span class="poet-profile__works-label">代表作</span>
                      <span class="poet-profile__works-list">{{ poetInfo.representative_works }}</span>
                    </div>
                    <div class="aside-card__foot">
                      <span class="aside-card__hint">数据来源：结构化诗人资料库</span>
                      <button type="button" class="aside-card__btn" @click="goAuthorArchive">查看全部作品</button>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <div v-if="currentTabContent" class="tab-text">{{ currentTabContent }}</div>
                  <div v-else class="tab-empty">暂无{{ currentTabLabel }}内容</div>
                </template>
              </div>
            </section>

            <section v-if="nextStepRecommendation" class="aside-card">
              <div class="aside-card__head">
                <div>
                  <p class="aside-card__eyebrow">NEXT READING</p>
                  <h2 class="aside-card__title">下一首建议</h2>
                </div>
                <span class="aside-card__badge">{{ nextStepRecommendation.badge }}</span>
              </div>
              <p class="aside-card__desc">{{ nextStepRecommendation.description }}</p>
              <div v-if="pathStepLabels.length" class="aside-steps">
                <span v-for="step in pathStepLabels" :key="step" class="aside-step">{{ step }}</span>
              </div>
              <button type="button" class="aside-recommend" @click="goToPoem(nextStepRecommendation.poem.id)">
                <div class="aside-recommend__main">
                  <h3 class="aside-recommend__title">{{ nextStepRecommendation.poem.title }}</h3>
                  <p class="aside-recommend__author">〔{{ nextStepRecommendation.poem.dynasty }}〕{{ nextStepRecommendation.poem.author }}</p>
                  <p class="aside-recommend__preview">{{ nextStepRecommendation.poem.content.split('\n').filter(Boolean).slice(0, 2).join(' / ') }}</p>
                </div>
                <div class="aside-recommend__foot">
                  <span class="aside-recommend__note">{{ nextStepRecommendation.footnote }}</span>
                  <span class="aside-recommend__action">继续研读</span>
                </div>
              </button>
            </section>

            <section class="aside-card" :class="{ 'aside-card--guest': !userStore.isLogin }">
              <div class="aside-card__head">
                <div>
                  <p class="aside-card__eyebrow">STUDY TRACE</p>
                  <h2 class="aside-card__title">{{ learningPanelTitle }}</h2>
                </div>
                <span class="aside-card__badge">{{ learningPanelBadge }}</span>
              </div>
              <p class="aside-card__desc">{{ learningPanelText }}</p>
              <div class="aside-stats">
                <article v-for="item in learningOverviewItems" :key="item.label" class="aside-stat">
                  <span class="aside-stat__label">{{ item.label }}</span>
                  <strong class="aside-stat__value">{{ item.value }}</strong>
                </article>
              </div>
              <div class="aside-card__foot">
                <span class="aside-card__hint">{{ learningPanelHint }}</span>
                <button type="button" class="aside-card__btn" @click="handleProgressAction">
                  {{ userStore.isLogin ? '查看卷宗进度' : '登录后记录轨迹' }}
                </button>
              </div>
            </section>
          </aside>

          <aside class="detail-aside">
            <section class="aside-card aside-card--ai aside-card--scrollable">
              <div class="aside-card__head">
                <div>
                  <p class="aside-card__eyebrow">AI STUDY</p>
                  <h2 class="aside-card__title">翰林助学</h2>
                </div>
                <span class="aside-card__badge aside-card__badge--accent">AI</span>
              </div>
              <div class="aside-card__scroll">
                <p class="aside-card__desc">{{ poetInfo ? '已加载诗人卷宗，可进一步请教 AI 翰林做深度解读。' : '可请教 AI 翰林为你解读诗人生平与诗词内涵。' }}</p>
                <div class="aside-entries">
                  <button
                    v-for="opt in aiQueryOptions"
                    :key="opt.key"
                    type="button"
                    class="aside-entry"
                    :class="{ 'aside-entry--active': aiActiveQuery === opt.key }"
                    @click="queryAI(opt.key)"
                  >
                    <span class="aside-entry__mark">{{ opt.mark }}</span>
                    <div class="aside-entry__info">
                      <span class="aside-entry__name">{{ opt.label }}</span>
                      <span class="aside-entry__sub">{{ opt.desc }}</span>
                    </div>
                  </button>
                </div>

                <div v-if="aiActiveQuery" class="ai-result-inline">
                  <div class="ai-result-inline__head">
                    <h3 class="ai-result-inline__title">{{ aiResult?.title || '正在请教翰林...' }}</h3>
                    <button type="button" class="ai-result-inline__close" @click="closeAIPanel">收起</button>
                  </div>
                  <div v-if="aiLoading" class="ai-panel__loading">
                    <div class="ai-panel__spinner"></div>
                    <span class="ai-panel__loading-text">翰林正在研墨撰文...</span>
                    <AiPhaseStatus
                      title="翰林助学生成中"
                      :stages="aiContextStages"
                      :current="aiContextStep"
                      hint="正在结合原文、作者与题材生成解读"
                    />
                  </div>
                  <div v-else-if="aiError" class="ai-panel__error">
                    <p class="ai-panel__error-text">{{ aiError }}</p>
                    <button type="button" class="ai-panel__retry" @click="queryAI(aiActiveQuery!)">重新请教</button>
                  </div>
                  <div v-else-if="aiResult" class="ai-panel__body">
                    <template v-if="aiResult.query_type === 'meter_analysis' && aiResult.lines">
                      <div class="meter-header">
                        <span v-if="aiResult.meter_type" class="meter-badge">{{ aiResult.meter_type }}</span>
                        <span v-if="aiResult.rhyme_scheme" class="meter-badge meter-badge--rhyme">{{ aiResult.rhyme_scheme }}</span>
                      </div>
                      <div v-if="aiResult.content" class="ai-panel__content">{{ aiResult.content }}</div>
                      <div class="meter-lines">
                        <div v-for="(line, idx) in aiResult.lines" :key="idx" class="meter-line">
                          <div class="meter-line__tones">
                            <span
                              v-for="(tone, ti) in line.tones"
                              :key="ti"
                              class="meter-tone"
                              :class="{
                                'meter-tone--ping': tone === '平',
                                'meter-tone--ze': tone === '仄',
                                'meter-tone--zhong': tone === '中',
                              }"
                            >{{ tone }}</span>
                          </div>
                          <div class="meter-line__chars">
                            <span
                              v-for="(ch, ci) in line.text.split('')"
                              :key="ci"
                              class="meter-char"
                              :class="{ 'meter-char--rhyme': line.rhyme && ci === line.text.length - 1 }"
                            >{{ ch }}</span>
                          </div>
                          <div class="meter-line__info">
                            <span v-if="line.rhyme" class="meter-tag meter-tag--rhyme">韵：{{ line.rhyme }}</span>
                            <span v-if="line.couplet" class="meter-tag meter-tag--couplet">{{ line.couplet }}</span>
                            <span v-if="line.note" class="meter-tag meter-tag--note">{{ line.note }}</span>
                          </div>
                        </div>
                      </div>
                    </template>
                    <template v-else>
                      <div v-if="aiResult.content" class="ai-panel__content">{{ aiResult.content }}</div>
                      <div v-if="aiResult.sections && aiResult.sections.length" class="ai-panel__sections">
                        <div v-for="(sec, idx) in aiResult.sections" :key="idx" class="ai-section">
                          <h3 class="ai-section__heading">{{ sec.heading }}</h3>
                          <p class="ai-section__text">{{ sec.text }}</p>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>

                <div class="ai-chat-inline">
                  <div class="ai-chat-inline__head">
                    <p class="ai-qa-box__label">问诗对话</p>
                    <span v-if="aiChatMessages.length" class="ai-chat-inline__count">{{ aiChatMessages.length }}条</span>
                  </div>
                  <div class="ai-chat-inline__messages">
                    <div v-if="aiChatMessages.length === 0 && !aiChatLoading" class="ai-chat-inline__empty">
                      输入问题，翰林将围绕这首诗与你对话
                    </div>
                    <div
                      v-for="(msg, idx) in aiChatMessages"
                      :key="idx"
                      class="ai-chat-msg"
                      :class="'ai-chat-msg--' + msg.role"
                    >
                      <span class="ai-chat-msg__role">{{ msg.role === 'user' ? '你' : '翰林' }}</span>
                      <p class="ai-chat-msg__text">{{ msg.content }}</p>
                    </div>
                    <div v-if="aiChatLoading && !aiChatMessages[aiChatMessages.length - 1]?.content" class="ai-chat-msg ai-chat-msg--assistant">
                      <span class="ai-chat-msg__role">翰林</span>
                      <p class="ai-chat-msg__text ai-chat-msg__typing">{{ aiChatStatus || '正在思索...' }}</p>
                    </div>
                  </div>
                  <div class="ai-qa-box__row">
                    <input
                      v-model="aiChatInput"
                      type="text"
                      class="ai-qa-box__input"
                      placeholder="关于这首诗，你想知道什么？"
                      maxlength="500"
                      @keydown.enter="sendChatMessage"
                    />
                    <button
                      type="button"
                      class="ai-qa-box__btn"
                      :disabled="!aiChatInput.trim() || aiChatLoading"
                      @click="sendChatMessage"
                    >问</button>
                  </div>
                </div>
              </div>
            </section>

            <section v-if="userStore.isLogin" class="aside-card">
              <div class="aside-card__head">
                <div>
                  <p class="aside-card__eyebrow">PRACTICE &amp; CREATE</p>
                  <h2 class="aside-card__title">以此诗为起点</h2>
                </div>
                <span class="aside-card__badge aside-card__badge--accent">学以致用</span>
              </div>
              <p class="aside-card__desc">从阅读到实践，用不同方式与这首诗互动。</p>
              <div class="aside-entries">
                <button type="button" class="aside-entry" @click="goToChallenge">
                  <span class="aside-entry__mark">笔</span>
                  <div class="aside-entry__info">
                    <span class="aside-entry__name">妙笔挑战</span>
                    <span class="aside-entry__sub">填词续写，以笔会诗</span>
                  </div>
                </button>
                <button type="button" class="aside-entry" @click="goToFeihualing">
                  <span class="aside-entry__mark">花</span>
                  <div class="aside-entry__info">
                    <span class="aside-entry__name">飞花令</span>
                    <span class="aside-entry__sub">以诗中字为令，限时吟诵</span>
                  </div>
                </button>
                <button type="button" class="aside-entry" @click="goToCreate">
                  <span class="aside-entry__mark">创</span>
                  <div class="aside-entry__info">
                    <span class="aside-entry__name">仿写创作</span>
                    <span class="aside-entry__sub">以此诗为灵感，挥毫泼墨</span>
                  </div>
                </button>
              </div>
            </section>
          </aside>
        </div>

        <div v-if="relatedPoems.length > 0 || themePoems.length > 0" class="related-tabbed">
          <div class="related-tabbed__header">
            <button
              v-if="relatedPoems.length > 0"
              type="button"
              class="related-tabbed__tab"
              :class="{ active: activeRelatedTab === 'author' }"
              @click="activeRelatedTab = 'author'"
            >同作者作品</button>
            <button
              v-if="themePoems.length > 0"
              type="button"
              class="related-tabbed__tab"
              :class="{ active: activeRelatedTab === 'theme' }"
              @click="activeRelatedTab = 'theme'"
            >{{ themeSectionTitle }}</button>
          </div>
          <div class="related-grid">
            <template v-if="activeRelatedTab === 'author'">
              <div
                v-for="rp in relatedPoems"
                :key="rp.id"
                class="related-card"
                @click="goToPoem(rp.id)"
              >
                <div class="related-card-title">{{ rp.title }}</div>
                <div class="related-card-author">〔{{ rp.dynasty }}〕{{ rp.author }}</div>
                <div class="related-card-preview">{{ rp.content.split('\n')[0] }}</div>
              </div>
            </template>
            <template v-else-if="activeRelatedTab === 'theme'">
              <div
                v-for="tp in themePoems"
                :key="tp.id"
                class="related-card"
                @click="goToPoem(tp.id)"
              >
                <div class="related-card-title">{{ tp.title }}</div>
                <div class="related-card-author">〔{{ tp.dynasty }}〕{{ tp.author }}</div>
                <div class="related-card-preview">{{ tp.content.split('\n')[0] }}</div>
              </div>
            </template>
          </div>
        </div>
      </template>

      <div v-else class="detail-empty">
        <div class="detail-empty__seal">卷</div>
        <h2 class="detail-empty__title">这卷诗作暂未找到</h2>
        <p class="detail-empty__text">可能当前卷目标识无效，或这首诗词尚未收录。你可以返回诗词学堂，或随机再读一首。</p>
        <div class="detail-empty__actions">
          <button type="button" class="detail-empty__button detail-empty__button--primary" @click="goBack">返回学堂</button>
          <button type="button" class="detail-empty__button" @click="openRandomPoem" :disabled="loadingRandom">
            {{ loadingRandom ? '寻卷中' : '随机一卷' }}
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showLinePickerModal" class="line-picker-overlay" @click.self="showLinePickerModal = false">
        <div class="line-picker-modal">
          <div class="line-picker__head">
            <h3 class="line-picker__title">选一句，作为妙笔题面</h3>
            <button type="button" class="line-picker__close" @click="showLinePickerModal = false">✕</button>
          </div>
          <p class="line-picker__hint">点击下方诗句，系统将自动挖空生成填字挑战</p>
          <div class="line-picker__lines">
            <button
              v-for="(line, idx) in poemLines"
              :key="idx"
              type="button"
              class="line-picker__line"
              :disabled="creatingChallenge"
              @click="pickLineForChallenge(line)"
            >{{ line }}</button>
          </div>
          <div v-if="creatingChallenge" class="line-picker__loading">正在生成挑战...</div>
        </div>
      </div>

      <div v-if="showFhlKeywordPicker" class="line-picker-overlay" @click.self="showFhlKeywordPicker = false">
        <div class="line-picker-modal fhl-kw-modal">
          <div class="line-picker__head">
            <h3 class="line-picker__title">选一字，作为飞花令字</h3>
            <button type="button" class="line-picker__close" @click="showFhlKeywordPicker = false">✕</button>
          </div>
          <p class="line-picker__hint">从这首诗中选取一个字作为令字，或自行输入</p>
          <div class="fhl-kw-grid">
            <button
              v-for="ch in fhlCandidateChars"
              :key="ch"
              type="button"
              class="fhl-kw-char"
              :class="{ 'fhl-kw-char--selected': fhlPickedChar === ch }"
              @click="fhlPickedChar = ch"
            >{{ ch }}</button>
          </div>
          <div class="fhl-kw-custom">
            <input
              v-model="fhlCustomChar"
              type="text"
              maxlength="1"
              class="fhl-kw-input"
              placeholder="自定义令字"
              @input="onFhlCustomInput"
            />
          </div>
          <div class="fhl-kw-preview" v-if="fhlFinalChar">
            <span class="fhl-kw-preview__label">令字</span>
            <span class="fhl-kw-preview__char">{{ fhlFinalChar }}</span>
          </div>
          <div class="fhl-kw-actions">
            <button
              type="button"
              class="fhl-kw-go"
              :disabled="!fhlFinalChar"
              @click="confirmGoFeihualing()"
            >开始飞花令</button>
            <button type="button" class="fhl-kw-random" @click="confirmGoFeihualing(true)">随机令字</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'
import { poemApi, type PoemDetail, type Poem } from '@/api/poem'
import { learningApi, type UserStats } from '@/api/learning'
import { challengeApi } from '@/api/challenge'
import { aiPoemChatStream, aiPoemContextStream, type PoemContextQueryType, type AIPoemContextResponse, type AIPoemChatMessage, type StreamEvent } from '@/api/ai'
import { useUserStore } from '@/store/modules/user'
import { poetApi, type PoetBrief } from '@/api/poet'
import AiPhaseStatus from '@/components/AiPhaseStatus.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const poem = ref<PoemDetail | null>(null)
const loading = ref(true)
const isScrolled = ref(false)
const isFavorited = ref(false)
const activeTab = ref('poet')
const activeRelatedTab = ref('author')
const relatedPoems = ref<Poem[]>([])
const themePoems = ref<Poem[]>([])
const dynastyPoems = ref<Poem[]>([])
const loadingRandom = ref(false)
const showLinePickerModal = ref(false)
const creatingChallenge = ref(false)
const showFhlKeywordPicker = ref(false)
const fhlPickedChar = ref('')
const fhlCustomChar = ref('')

const poetInfo = ref<PoetBrief | null>(null)
const loadingPoet = ref(false)

const aiActiveQuery = ref<PoemContextQueryType | null>(null)
const aiLoading = ref(false)
const aiResult = ref<AIPoemContextResponse | null>(null)
const aiError = ref('')
const aiQuestion = ref('')
const aiHistory = new Map<string, AIPoemContextResponse>()
const aiContextStep = ref(0)
const aiContextStages = ref<string[]>([])
const aiContextTimer = ref<number | null>(null)

const aiChatMessages = ref<AIPoemChatMessage[]>([])
const aiChatInput = ref('')
const aiChatLoading = ref(false)
const aiChatOpen = ref(false)
const aiChatStatus = ref('')

const aiQueryOptions: { key: PoemContextQueryType; label: string; mark: string; desc: string }[] = [
  { key: 'author_bio', label: '诗人小传', mark: '传', desc: '生平经历与文学风格' },
  { key: 'deep_appreciation', label: '深度赏析', mark: '赏', desc: 'AI 解读意境与手法' },
  { key: 'allusions', label: '典故意象', mark: '典', desc: '典故出处与文化内涵' },
  { key: 'verse_analysis', label: '逐句精析', mark: '析', desc: '逐句解读炼字之妙' },
  { key: 'meter_analysis', label: '格律标注', mark: '律', desc: '平仄韵脚对仗可视化' },
]

const aiContextStagesMap: Record<PoemContextQueryType, string[]> = {
  author_bio: ['整理作者信息', '提炼生平线索', '生成小传总结'],
  deep_appreciation: ['解析诗句结构', '提炼意境手法', '生成深度赏析'],
  allusions: ['识别典故意象', '定位文化语境', '生成典故解读'],
  verse_analysis: ['逐句拆解', '分析炼字用意', '汇总逐句精析'],
  meter_analysis: ['识别格律格式', '标注平仄韵脚', '输出格律说明'],
  free_qa: ['理解提问焦点', '匹配诗句证据', '生成问答结论'],
}

const clearAIContextTimer = () => {
  if (aiContextTimer.value !== null) {
    clearInterval(aiContextTimer.value)
    aiContextTimer.value = null
  }
}
const loadingStats = ref(false)
const learningStats = ref<UserStats | null>(null)
const sessionElapsedSeconds = ref(0)
const sessionPoemId = ref<number | null>(null)
const sessionStartedAt = ref<number | null>(null)

let sessionTicker: ReturnType<typeof window.setInterval> | null = null
const handledSessionKeys = new Set<string>()

const allTabs = [
  { key: 'poet', label: '诗人卷宗' },
  { key: 'annotation', label: '注释' },
  { key: 'background', label: '创作背景' },
  { key: 'appreciation', label: '赏析' }
]

const availableTabs = computed(() => {
  if (!poem.value) return []

  return allTabs.filter(tab => {
    if (tab.key === 'poet') return Boolean(poetInfo.value)
    const contentMap: Record<string, string | undefined> = {
      annotation: poem.value?.annotation,
      background: poem.value?.background,
      appreciation: poem.value?.appreciation
    }

    return Boolean(contentMap[tab.key]?.trim())
  })
})

const currentTabLabel = computed(() => {
  return availableTabs.value.find(t => t.key === activeTab.value)?.label || ''
})

const currentTabContent = computed(() => {
  if (!poem.value || activeTab.value === 'poet') return ''
  const map: Record<string, string | undefined> = {
    annotation: poem.value.annotation,
    background: poem.value.background,
    appreciation: poem.value.appreciation
  }
  return map[activeTab.value] || ''
})

const poemLines = computed(() => {
  if (!poem.value) return []
  return poem.value.content.split('\n').filter(line => line.trim())
})

const studyGuideText = computed(() => {
  if (!poem.value) return ''

  const intro = `这是一首${poem.value.dynasty}代${poem.value.author}的${poem.value.genre || '诗作'}。`

  if (poem.value.category) {
    return `${intro}建议先从「${poem.value.category}」主题切入，再对照译文、注释与赏析体会其意脉与情感层次。`
  }

  return `${intro}建议先通读原文，再结合译文与赏析理解关键意象、情绪转折与用字节奏。`
})

const quickFacts = computed(() => {
  if (!poem.value) return []

  return [
    {
      label: '体裁',
      value: poem.value.genre || '未标注'
    },
    {
      label: '题材',
      value: poem.value.category || '未标注'
    },
    {
      label: '诗行',
      value: `${poemLines.value.length}行`
    },
    {
      label: '收藏状态',
      value: userStore.isLogin ? (isFavorited.value ? '已收藏' : '未收藏') : '登录后可收藏'
    }
  ]
})

const themeSectionTitle = computed(() => {
  if (!poem.value) return '延展阅读'
  if (poem.value.category) return '同题材延展'
  if (poem.value.genre) return '同体裁延展'
  return '延展阅读'
})

const dynastySectionTitle = computed(() => {
  if (!poem.value) return '同朝代对读'
  return `${poem.value.dynasty}代对读`
})

const pathStepLabels = computed(() => {
  const steps: string[] = []

  if (relatedPoems.value.length) {
    steps.push('同作者深入')
  }

  if (themePoems.value.length) {
    steps.push(themeSectionTitle.value)
  }

  if (dynastyPoems.value.length) {
    steps.push(dynastySectionTitle.value)
  }

  return steps
})

const nextStepRecommendation = computed(() => {
  if (!poem.value) return null

  const authorCandidate = relatedPoems.value.find(item => {
    return (poem.value?.genre && item.genre === poem.value.genre) || (poem.value?.category && item.category === poem.value.category)
  }) || relatedPoems.value[0]

  if (authorCandidate) {
    return {
      poem: authorCandidate,
      badge: '先读同作者',
      description: `先沿着 ${poem.value.author} 的另一首作品继续深入，更容易保持语言气息与情绪脉络的连续理解。`,
      footnote: authorCandidate.genre === poem.value.genre ? `与当前同为${poem.value.genre}` : '延续作者笔法'
    }
  }

  const themeCandidate = themePoems.value[0]
  if (themeCandidate) {
    return {
      poem: themeCandidate,
      badge: poem.value.category ? '同题材延展' : '同体裁延展',
      description: poem.value.category
        ? `把视角切到同一题材的其他作品，能更快建立「${poem.value.category}」主题的意象对照与情感层次。`
        : `切到相同体裁的作品继续阅读，便于体会 ${poem.value.genre || '诗作'} 的节奏与结构。`,
      footnote: poem.value.category ? `围绕${poem.value.category}展开` : `延展${poem.value.genre || '诗作'}阅读`
    }
  }

  const dynastyCandidate = dynastyPoems.value[0]
  if (dynastyCandidate) {
    return {
      poem: dynastyCandidate,
      badge: '同朝代对读',
      description: `把这首作品放回 ${poem.value.dynasty} 代语境继续对读，有助于建立时代横向比较，而不只停留在单首理解。`,
      footnote: `建立${poem.value.dynasty}代语境感`
    }
  }

  return null
})

const sessionDurationText = computed(() => formatDuration(sessionElapsedSeconds.value))

const learningPanelTitle = computed(() => {
  return userStore.isLogin ? '我的研习反馈' : '研习轨迹待落款'
})

const learningPanelBadge = computed(() => {
  if (!userStore.isLogin) return '登录后开启'
  if (loadingStats.value && !learningStats.value) return '同步中'
  return '已接入卷宗'
})

const learningOverviewItems = computed(() => {
  if (userStore.isLogin) {
    return [
      {
        label: '本次研读',
        value: sessionDurationText.value
      },
      {
        label: '已学诗词',
        value: `${learningStats.value?.total_learned ?? 0}首`
      },
      {
        label: '累计研习',
        value: formatDuration(learningStats.value?.study_time ?? 0)
      },
      {
        label: '连续研习',
        value: `${learningStats.value?.streak_days ?? 0}天`
      }
    ]
  }

  return [
    {
      label: '本次停留',
      value: sessionDurationText.value
    },
    {
      label: '学习轨迹',
      value: '登录后开启'
    },
    {
      label: '卷宗同步',
      value: '自动记录'
    },
    {
      label: '收藏卷柜',
      value: '登录后可用'
    }
  ]
})

const learningPanelText = computed(() => {
  if (userStore.isLogin) {
    const learnedCount = learningStats.value?.total_learned ?? 0
    const streakDays = learningStats.value?.streak_days ?? 0
    return `当前这卷的阅读时长会在你切换下一卷或离开页面时写入卷宗。你已累计研读 ${learnedCount} 首诗词，连续研习 ${streakDays} 天。`
  }

  return '登录后，当前诗卷的阅读时长与学习次数会自动沉淀到个人卷宗，回到个人中心即可查看成长曲线。'
})

const learningPanelHint = computed(() => {
  if (userStore.isLogin) {
    return '继续停留、切换下一卷或返回学堂时，系统会把本次研读计入你的学习轨迹。'
  }

  return '登录后即可自动记录研习时长、已学诗词与连续研习天数。'
})

const formatDuration = (seconds: number) => {
  if (!seconds) return '0秒'
  if (seconds < 60) return `${seconds}秒`

  const totalMinutes = Math.max(1, Math.round(seconds / 60))
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  if (hours && minutes) return `${hours}时${minutes}分`
  if (hours) return `${hours}时`
  return `${totalMinutes}分`
}

const stopSessionTicker = () => {
  if (sessionTicker !== null) {
    window.clearInterval(sessionTicker)
    sessionTicker = null
  }
}

const resetLearningSession = () => {
  stopSessionTicker()
  sessionElapsedSeconds.value = 0
  sessionPoemId.value = null
  sessionStartedAt.value = null
}

const updateSessionElapsed = () => {
  if (!sessionStartedAt.value) {
    sessionElapsedSeconds.value = 0
    return
  }

  sessionElapsedSeconds.value = Math.max(1, Math.floor((Date.now() - sessionStartedAt.value) / 1000))
}

const startLearningSession = (poemId: number) => {
  resetLearningSession()
  sessionPoemId.value = poemId
  sessionStartedAt.value = Date.now()
  sessionElapsedSeconds.value = 1
  sessionTicker = window.setInterval(updateSessionElapsed, 1000)
}

const loadLearningStats = async () => {
  if (!userStore.isLogin) {
    learningStats.value = null
    return
  }

  loadingStats.value = true
  try {
    learningStats.value = await learningApi.getStats()
  } catch (error) {
    console.error('加载学习统计失败:', error)
  } finally {
    loadingStats.value = false
  }
}

const flushLearningSession = async () => {
  const poemId = sessionPoemId.value
  const startedAt = sessionStartedAt.value

  if (!poemId || !startedAt) {
    resetLearningSession()
    return
  }

  const sessionKey = `${poemId}-${startedAt}`
  if (handledSessionKeys.has(sessionKey)) {
    resetLearningSession()
    return
  }

  const duration = Math.max(1, Math.round((Date.now() - startedAt) / 1000))

  handledSessionKeys.add(sessionKey)
  resetLearningSession()

  if (!userStore.isLogin || duration < 8) return

  try {
    await learningApi.recordLearning({
      poem_id: poemId,
      action: 'view',
      duration
    })
    void userStore.fetchUserInfo()
    void loadLearningStats()
  } catch (error) {
    console.error('记录学习进度失败:', error)
  }
}

const getPathFitScore = (currentPoem: PoemDetail, candidate: Poem) => {
  let score = 0

  if (currentPoem.genre && candidate.genre === currentPoem.genre) {
    score += 3
  }

  if (currentPoem.category && candidate.category === currentPoem.category) {
    score += 2
  }

  const currentLineCount = currentPoem.content.split('\n').filter(line => line.trim()).length
  const candidateLineCount = candidate.content.split('\n').filter(line => line.trim()).length

  score -= Math.min(1.5, Math.abs(currentLineCount - candidateLineCount) * 0.25)

  return score
}

const sortCandidatesByPathFit = (currentPoem: PoemDetail, items: Poem[]) => {
  return [...items].sort((left, right) => {
    return getPathFitScore(currentPoem, right) - getPathFitScore(currentPoem, left)
  })
}

const loadPoem = async (id: number) => {
  loading.value = true
  resetAIState()
  poem.value = null
  relatedPoems.value = []
  themePoems.value = []
  dynastyPoems.value = []
  try {
    const currentPoem = await poemApi.getDetail(id)
    poem.value = currentPoem
    isFavorited.value = currentPoem.is_favorited
    activeTab.value = availableTabs.value[0]?.key || 'poet'
    poem.value.view_count += 1
    startLearningSession(currentPoem.id)
    if (userStore.isLogin) {
      void loadLearningStats()
    } else {
      learningStats.value = null
    }
    poemApi.incrementView(id).catch(() => {})
    void loadPoetInfo(currentPoem.author, currentPoem.dynasty)
    await loadRecommendations(currentPoem)
  } catch (error) {
    resetLearningSession()
    resetAIState()
    poem.value = null
    relatedPoems.value = []
    themePoems.value = []
    dynastyPoems.value = []
    console.error('加载诗词失败:', error)
  } finally {
    loading.value = false
  }
}

const loadPoetInfo = async (authorName: string, dynasty: string) => {
  loadingPoet.value = true
  poetInfo.value = null
  try {
    const result = await poetApi.getByName(authorName, dynasty)
    poetInfo.value = result
  } catch {
    poetInfo.value = null
  } finally {
    loadingPoet.value = false
  }
}

const loadRecommendations = async (currentPoem: PoemDetail) => {
  const themeRequest = currentPoem.category
    ? poemApi.getList({ category: currentPoem.category, page: 1, page_size: 6 })
    : currentPoem.genre
      ? poemApi.getList({ genre: currentPoem.genre, page: 1, page_size: 6 })
      : Promise.resolve({ items: [], total: 0, page: 1, page_size: 6 })

  const dynastyRequest = poemApi.getList({ dynasty: currentPoem.dynasty, page: 1, page_size: 8 })

  const [authorResult, themeResult, dynastyResult] = await Promise.allSettled([
    poemApi.search({
      keyword: currentPoem.author,
      search_type: 'author',
      page: 1,
      page_size: 6
    }),
    themeRequest,
    dynastyRequest
  ])

  const authorItems = authorResult.status === 'fulfilled'
    ? sortCandidatesByPathFit(
      currentPoem,
      authorResult.value.items.filter(item => item.id !== currentPoem.id)
    ).slice(0, 4)
    : []

  const authorIds = new Set(authorItems.map(item => item.id))

  const themeItems = themeResult.status === 'fulfilled'
    ? sortCandidatesByPathFit(
      currentPoem,
      themeResult.value.items.filter(item => item.id !== currentPoem.id && !authorIds.has(item.id) && item.author !== currentPoem.author)
    ).slice(0, 4)
    : []

  const usedIds = new Set([...authorIds, ...themeItems.map(item => item.id)])

  const dynastyItems = dynastyResult.status === 'fulfilled'
    ? sortCandidatesByPathFit(
      currentPoem,
      dynastyResult.value.items.filter(item => item.id !== currentPoem.id && !usedIds.has(item.id) && item.author !== currentPoem.author)
    ).slice(0, 4)
    : []

  relatedPoems.value = authorItems
  themePoems.value = themeItems
  dynastyPoems.value = dynastyItems

  if (authorItems.length > 0) {
    activeRelatedTab.value = 'author'
  } else if (themeItems.length > 0) {
    activeRelatedTab.value = 'theme'
  }
}

const toggleFavorite = async () => {
  if (!poem.value) return
  try {
    if (isFavorited.value) {
      await poemApi.unfavorite(poem.value.id)
      isFavorited.value = false
      poem.value.favorite_count = Math.max(0, poem.value.favorite_count - 1)
      if (learningStats.value) {
        learningStats.value.total_favorites = Math.max(0, learningStats.value.total_favorites - 1)
      }
    } else {
      await poemApi.favorite(poem.value.id)
      isFavorited.value = true
      poem.value.favorite_count += 1
      if (learningStats.value) {
        learningStats.value.total_favorites += 1
      }
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
  }
}

const handleProgressAction = () => {
  if (userStore.isLogin) {
    router.push({
      path: '/profile/folio',
      query: {
        tab: 'progress'
      }
    })
    return
  }

  router.push('/login')
}

const openRandomPoem = async () => {
  try {
    loadingRandom.value = true
    const randomPoem = await poemApi.getRandom(poem.value?.dynasty)
    router.push(`/poems/${randomPoem.id}`)
  } catch (error) {
    console.error('随机诗词加载失败:', error)
  } finally {
    loadingRandom.value = false
  }
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/poems')
  }
}

const goToPoem = (id: number) => {
  router.push(`/poems/${id}`)
}

const goAuthorArchive = () => {
  if (!poem.value) return

  router.push({
    path: '/poems',
    query: {
      q: poem.value.author,
      searchType: 'author'
    }
  })
}

const queryAI = async (queryType: PoemContextQueryType, question?: string) => {
  if (!poem.value || aiLoading.value) return

  const cacheKey = `${poem.value.id}-${queryType}-${question || ''}`
  const cached = aiHistory.get(cacheKey)
  if (cached) {
    aiActiveQuery.value = queryType
    aiResult.value = cached
    aiError.value = ''
    return
  }

  aiActiveQuery.value = queryType
  aiLoading.value = true
  aiError.value = ''
  aiResult.value = null
  aiContextStages.value = aiContextStagesMap[queryType] || ['解析请求', '整理上下文', '生成结果']
  aiContextStep.value = 0
  clearAIContextTimer()

  try {
    await aiPoemContextStream(
      {
        title: poem.value.title,
        author: poem.value.author,
        dynasty: poem.value.dynasty,
        content: poem.value.content,
        genre: poem.value.genre || undefined,
        category: poem.value.category || undefined,
        query_type: queryType,
        question,
      },
      (_event: StreamEvent) => {
        if (aiContextStep.value < aiContextStages.value.length - 1) {
          aiContextStep.value++
        }
      },
      (result: AIPoemContextResponse) => {
        aiResult.value = result
        aiHistory.set(cacheKey, result)
      },
      (err: string) => {
        aiError.value = err
      },
    )
  } catch (error: any) {
    aiError.value = error?.response?.data?.detail || 'AI 助学服务暂时不可用，请稍后再试'
  } finally {
    clearAIContextTimer()
    aiContextStep.value = 0
    aiLoading.value = false
  }
}

const closeAIPanel = () => {
  aiActiveQuery.value = null
  aiResult.value = null
  aiError.value = ''
}

const resetAIState = () => {
  closeAIPanel()
  aiQuestion.value = ''
  aiHistory.clear()
  aiChatMessages.value = []
  aiChatInput.value = ''
  aiChatLoading.value = false
  aiChatOpen.value = false
}

const sendChatMessage = async () => {
  const msg = aiChatInput.value.trim()
  if (!msg || !poem.value || aiChatLoading.value) return

  aiChatInput.value = ''
  aiChatOpen.value = true
  aiChatMessages.value.push({ role: 'user', content: msg })
  aiChatLoading.value = true
  aiChatStatus.value = ''

  const assistantIdx = aiChatMessages.value.length
  aiChatMessages.value.push({ role: 'assistant', content: '' })

  try {
    await aiPoemChatStream(
      {
        title: poem.value.title,
        author: poem.value.author,
        dynasty: poem.value.dynasty,
        content: poem.value.content,
        genre: poem.value.genre || undefined,
        category: poem.value.category || undefined,
        history: aiChatMessages.value.slice(0, assistantIdx - 1),
        message: msg,
      },
      (chunk: string) => {
        aiChatStatus.value = ''
        const assistantMessage = aiChatMessages.value[assistantIdx]
        if (assistantMessage) {
          assistantMessage.content += chunk
        }
      },
      () => {
        aiChatLoading.value = false
        aiChatStatus.value = ''
      },
      (err: string) => {
        const assistantMessage = aiChatMessages.value[assistantIdx]
        if (assistantMessage) {
          assistantMessage.content = err || '抱歉，翰林暂时无法作答，请稍后再试。'
        }
        aiChatLoading.value = false
        aiChatStatus.value = ''
      },
      (event: StreamEvent) => {
        if (event.type === 'thinking') {
          aiChatStatus.value = event.content || '正在思索...'
        } else if (event.type === 'tool_call') {
          const labels = event.labels || event.tools || []
          aiChatStatus.value = `正在${labels.join('、')}...`
        } else if (event.type === 'memory') {
          aiChatStatus.value = event.content || '记忆已加载'
        }
      },
    )
  } catch {
    const assistantMessage = aiChatMessages.value[assistantIdx]
    if (assistantMessage) {
      assistantMessage.content = '抱歉，翰林暂时无法作答，请稍后再试。'
    }
    aiChatLoading.value = false
    aiChatStatus.value = ''
  }
}

const goToChallenge = () => {
  if (poem.value && poemLines.value.length > 0) {
    showLinePickerModal.value = true
    return
  }
  router.push('/challenge')
}

const blankOneLine = (src: string): { template: string; answer: string } | null => {
  const chars = src.replace(/[，。！？；、\s]/g, '')
  if (chars.length < 3) return null
  const blankIdx = Math.floor(Math.random() * chars.length)
  let template = ''
  let answer = ''
  let ci = 0
  for (const ch of src) {
    if (/[，。！？；、\s]/.test(ch)) {
      template += ch
    } else {
      if (ci === blankIdx) {
        template += '_'
        answer = ch
      } else {
        template += ch
      }
      ci++
    }
  }
  return { template, answer }
}

const pickLineForChallenge = async (line: string) => {
  if (creatingChallenge.value || !poem.value) return
  creatingChallenge.value = true
  try {
    const result1 = blankOneLine(line)
    if (!result1) {
      router.push('/challenge')
      return
    }

    let template2: string | undefined
    let answer2: string | undefined
    const allLines = poemLines.value
    const curIdx = allLines.indexOf(line)
    if (curIdx >= 0) {
      const pairLine = curIdx < allLines.length - 1
        ? allLines[curIdx + 1]
        : curIdx > 0 ? allLines[curIdx - 1] : null
      if (pairLine) {
        const r2 = blankOneLine(pairLine)
        if (r2) {
          template2 = r2.template
          answer2 = r2.answer
        }
      }
    }

    const created = await challengeApi.create({
      challenge_type: 'fill_blank',
      sentence_template: result1.template,
      sentence_template_2: template2,
      blank_count: 1,
      original_answer: result1.answer,
      original_answer_2: answer2,
      theme: poem.value.category || undefined,
      hint: `出自${poem.value.dynasty}·${poem.value.author}《${poem.value.title}》`,
      difficulty: 'medium',
    })
    showLinePickerModal.value = false
    router.push({ path: '/challenge', query: { challenge_id: String(created.id) } })
  } catch {
    router.push('/challenge')
  } finally {
    creatingChallenge.value = false
  }
}

const COMMON_STOPWORDS = new Set('的了是在不有人我他她它们这那个上下大小多少中为与而也就都要会可以从到被把让给用和得着过去来自己之于所以因如何其与乎者矣也哉兮而乃则虽然但且或若如此于是因为所以'.split(''))

const fhlCandidateChars = computed(() => {
  if (!poem.value) return []
  const content = poem.value.content
  const chars = content.replace(/[，。！？；、：""''\s\n\r\d\w]/g, '')
  const freq = new Map<string, number>()
  for (const ch of chars) {
    if (!COMMON_STOPWORDS.has(ch)) {
      freq.set(ch, (freq.get(ch) || 0) + 1)
    }
  }
  return [...freq.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(([ch]) => ch)
})

const fhlFinalChar = computed(() => {
  if (fhlCustomChar.value.trim()) return fhlCustomChar.value.trim()
  return fhlPickedChar.value
})

const onFhlCustomInput = () => {
  if (fhlCustomChar.value.trim()) {
    fhlPickedChar.value = ''
  }
}

const goToFeihualing = () => {
  fhlPickedChar.value = ''
  fhlCustomChar.value = ''
  showFhlKeywordPicker.value = true
}

const confirmGoFeihualing = (random?: boolean) => {
  showFhlKeywordPicker.value = false
  const kw = random ? undefined : fhlFinalChar.value || undefined
  const q: Record<string, string> = {}
  if (kw) q.keyword = kw
  if (poem.value) {
    q.from_poem = String(poem.value.id)
    q.from_title = poem.value.title
  }
  router.push({ path: '/games/feihualing', query: q })
}

const goToCreate = () => {
  if (!poem.value) {
    router.push('/works/create')
    return
  }
  router.push({
    path: '/works/create',
    query: {
      mode: 'imitate',
      ref_id: String(poem.value.id),
      ref_title: poem.value.title,
      ref_author: poem.value.author,
      ref_dynasty: poem.value.dynasty,
      ref_genre: poem.value.genre || undefined
    }
  })
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 20
}

watch(availableTabs, (tabs) => {
  if (!tabs.length) {
    activeTab.value = 'poet'
    return
  }

  if (!tabs.some(tab => tab.key === activeTab.value)) {
    const firstTab = tabs[0]
    if (firstTab) {
      activeTab.value = firstTab.key
    }
  }
})

watch(
  () => userStore.isLogin,
  (isLogin) => {
    if (isLogin) {
      void loadLearningStats()
      return
    }

    learningStats.value = null
  }
)

onBeforeRouteUpdate(() => {
  void flushLearningSession()
})

onBeforeRouteLeave(() => {
  void flushLearningSession()
})

watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      const id = Number(newId)
      if (!isNaN(id)) {
        loadPoem(id)
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }
  }
)

onMounted(() => {
  const id = Number(route.params.id)
  if (!isNaN(id)) {
    loadPoem(id)
  }
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  void flushLearningSession()
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped src="./styles/detail.css"></style>

<style>
.aside-card--scrollable {
  scrollbar-width: thin;
  scrollbar-color: rgba(178, 141, 87, 0.22) transparent;
}

.aside-card--scrollable::-webkit-scrollbar {
  width: 5px;
}

.aside-card--scrollable::-webkit-scrollbar-track {
  background: transparent;
  margin: 8px 0;
}

.aside-card--scrollable::-webkit-scrollbar-thumb {
  background: rgba(178, 141, 87, 0.22);
  border-radius: 6px;
}

.aside-card--scrollable::-webkit-scrollbar-thumb:hover {
  background: rgba(178, 141, 87, 0.38);
}
</style>
