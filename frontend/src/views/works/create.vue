<template>
  <div class="create-page">
    <div class="ink-bg">
      <div class="ink-wash ink-wash--1"></div>
      <div class="ink-wash ink-wash--2"></div>
    </div>

    <nav class="create-nav">
      <button class="nav-back" @click="goBack">← 返回</button>
      <span class="nav-title">{{ isImitateMode ? '仿写创作' : '诗词创作' }}</span>
      <div class="nav-actions">
        <button class="btn-save" @click="saveDraft" :disabled="saving">
          {{ saving ? '保存中…' : '存草稿' }}
        </button>
        <button class="btn-publish" @click="publishWork" :disabled="!canPublish || publishing">
          {{ publishing ? '发布中…' : '发布作品' }}
        </button>
      </div>
    </nav>

    <main class="create-body">
      <section class="editor-panel">
        <div class="editor-card">
          <div class="card-seal">{{ isImitateMode ? '仿' : '创' }}</div>

          <div v-if="isImitateMode && imitatePoem" class="imitate-banner">
            <div class="imitate-banner__head">
              <span class="imitate-banner__badge">仿写模式</span>
              <button type="button" class="imitate-banner__exit" @click="exitImitateMode">退出仿写</button>
            </div>
            <div class="imitate-banner__poem">
              <h4 class="imitate-banner__title">{{ imitatePoem.title }}</h4>
              <p class="imitate-banner__author">〔{{ imitatePoem.dynasty }}〕{{ imitatePoem.author }}</p>
              <div class="imitate-banner__preview">
                <p v-for="(line, i) in imitatePoemLines.slice(0, 4)" :key="i" class="imitate-banner__line">{{ line }}</p>
                <p v-if="imitatePoemLines.length > 4" class="imitate-banner__more">... 共{{ imitatePoemLines.length }}行</p>
              </div>
            </div>
            <div class="imitate-banner__struct">
              <span class="imitate-banner__struct-label">结构</span>
              <span class="imitate-banner__struct-value">{{ imitateStructDesc }}</span>
            </div>
            <div class="imitate-banner__actions">
              <button type="button" class="imitate-banner__action imitate-banner__action--primary" @click="applyImitateTemplate">载入仿写骨架</button>
              <button type="button" class="imitate-banner__action" @click="viewFullRef">查看原诗全文</button>
            </div>
          </div>

          <div class="field-group">
            <label class="field-label">作品标题</label>
            <input
              v-model="form.title"
              class="field-input"
              placeholder="为你的作品取一个名字"
              maxlength="200"
            />
          </div>

          <div class="field-group">
            <label class="field-label">选择体裁</label>
            <div class="genre-grid">
              <button
                v-for="g in genres"
                :key="g.value"
                class="genre-chip"
                :class="{ 'genre-chip--active': form.genre === g.value }"
                @click="form.genre = g.value"
              >
                <span class="genre-glyph">{{ g.glyph }}</span>
                <span class="genre-name">{{ g.label }}</span>
              </button>
            </div>
          </div>

          <div v-if="showStarterGuide" class="starter-guide">
            <div class="starter-guide__header">
              <span class="starter-guide__badge">初次落笔</span>
              <span class="starter-guide__note">先定题眼，再起首句</span>
            </div>
            <p class="starter-guide__text">如果你还不知道从哪里开始，可以用 AI 生成一首诗，或找一首名篇作为参考。</p>
            <div class="starter-guide__actions">
              <button type="button" class="starter-guide__action starter-guide__action--primary" @click="prepareAIGenerate()">AI 主题生成</button>
              <button type="button" class="starter-guide__action" @click="openReferencePanel">参考名篇</button>
            </div>
            <div class="starter-guide__topics">
              <button
                v-for="topic in starterTopics"
                :key="topic"
                type="button"
                class="starter-guide__topic"
                @click="applyStarterTopic(topic)"
              >
                {{ topic }}
              </button>
            </div>
          </div>

          <div class="field-group field-group--grow">
            <label class="field-label">
              诗词正文
              <span class="field-hint">{{ contentHint }}</span>
            </label>
            <textarea
              v-model="form.content"
              class="field-textarea"
              :class="{ 'field-textarea--flash': textareaFlash }"
              :placeholder="currentPlaceholder"
              @input="onContentInput"
            ></textarea>
            <div class="textarea-footer">
              <span v-if="lastSavedAt" class="auto-save-hint">
                <span class="auto-save-dot" :class="{ 'auto-save-dot--unsaved': hasUnsavedChanges }"></span>
                {{ hasUnsavedChanges ? '有未保存修改' : `已保存 ${lastSavedAt}` }}
              </span>
              <span class="char-count">
                <template v-if="expectedLineCount && contentLineCount">
                  <span class="line-count" :class="`line-count--${lineCountStatus}`">{{ contentLineCount }}/{{ expectedLineCount }}句</span>
                  <span class="count-sep">·</span>
                </template>
                {{ form.content.length }} 字
              </span>
            </div>

            <div class="ai-toolbar">
              <span class="ai-toolbar__label">AI</span>
              <div class="ai-toolbar__actions">
                <button
                  class="ai-btn"
                  :class="{ 'ai-btn--active': aiMode === 'continue' }"
                  :disabled="!form.content.trim() || aiLoading"
                  title="基于当前内容续写下一句"
                  @click="triggerAI('continue')"
                >
                  <svg class="ai-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                  <span>续写</span>
                </button>
                <button
                  class="ai-btn"
                  :class="{ 'ai-btn--active': aiMode === 'inspire' }"
                  :disabled="aiLoading"
                  title="获取创作灵感与意象建议"
                  @click="triggerAI('inspire')"
                >
                  <svg class="ai-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"/><line x1="10" y1="22" x2="14" y2="22"/></svg>
                  <span>灵感</span>
                </button>
                <button
                  class="ai-btn"
                  :class="{ 'ai-btn--active': aiMode === 'generate' }"
                  :disabled="aiLoading"
                  title="输入关键词生成完整诗词"
                  @click="showGenerateInput = !showGenerateInput; aiMode = 'generate'"
                >
                  <svg class="ai-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="m8 8 4-4 4 4"/><path d="M4 14h16"/></svg>
                  <span>生成</span>
                </button>
                <button
                  class="ai-btn"
                  :class="{ 'ai-btn--active': aiMode === 'check' }"
                  :disabled="!form.content.trim() || aiLoading"
                  title="检查平仄、押韵、对仗"
                  @click="triggerAI('check')"
                >
                  <svg class="ai-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                  <span>格律</span>
                </button>
                <button
                  class="ai-btn"
                  :class="{ 'ai-btn--active': aiMode === 'analyze' }"
                  :disabled="!form.content.trim() || aiLoading"
                  title="AI赏析与四维评分"
                  @click="triggerAI('analyze')"
                >
                  <svg class="ai-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                  <span>评分</span>
                </button>
                <button
                  v-if="isImitateMode && imitatePoem"
                  class="ai-btn ai-btn--imitate"
                  :class="{ 'ai-btn--active': aiMode === 'imitate_guide' }"
                  :disabled="aiLoading"
                  title="分析原诗风格，获取仿写指导建议"
                  @click="triggerAI('imitate_guide')"
                >
                  <svg class="ai-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                  <span>仿写建议</span>
                </button>
              </div>
            </div>

            <div v-if="showGenerateInput" class="ai-keywords-row">
              <input
                v-model="aiKeywords"
                class="ai-keywords-input"
                placeholder="输入主题或关键词，如：春日、离别、明月…"
                @keyup.enter="triggerAI('generate')"
              />
              <button
                class="ai-keywords-go"
                :disabled="!aiKeywords.trim() || aiLoading"
                @click="triggerAI('generate')"
              >生成诗词</button>
            </div>
          </div>
        </div>

        <div v-if="editingId" class="draft-info">
          <span class="draft-dot"></span>
          正在编辑草稿 #{{ editingId }}
        </div>

        <div class="ref-panel">
          <button type="button" class="ref-toggle" @click="refOpen = !refOpen">
            <span class="ref-toggle__mark">鉴</span>
            <span>{{ refOpen ? '收起参考诗词' : '展开参考诗词' }}</span>
          </button>

          <div v-if="refOpen" class="ref-body">
            <div v-if="refPoem" class="ref-card ref-card--from">
              <div class="ref-card__header">
                <span class="ref-card__badge">灵感来源</span>
                <button type="button" class="ref-card__close" @click="refPoem = null">&times;</button>
              </div>
              <h4 class="ref-card__title">{{ refPoem.title }}</h4>
              <p class="ref-card__author">〔{{ refPoem.dynasty }}〕{{ refPoem.author }}</p>
              <div class="ref-card__content">
                <p v-for="(line, i) in refPoem.content.split('\n').filter(Boolean).slice(0, 6)" :key="i" class="ref-card__line">{{ line }}</p>
                <p v-if="refPoem.content.split('\n').filter(Boolean).length > 6" class="ref-card__more">...</p>
              </div>
            </div>

            <div class="ref-search">
              <input
                ref="refSearchInputEl"
                v-model="refQuery"
                class="ref-search__input"
                placeholder="搜索诗词作为参考..."
                @keyup.enter="searchRefPoems"
              />
              <button type="button" class="ref-search__btn" @click="searchRefPoems" :disabled="refSearching">检索</button>
            </div>

            <div v-if="refSearching" class="ref-loading">检索中...</div>
            <div v-else-if="refResults.length" class="ref-results">
              <div
                v-for="p in refResults"
                :key="p.id"
                class="ref-card ref-card--result"
                @click="expandedRefId = expandedRefId === p.id ? null : p.id"
              >
                <h4 class="ref-card__title">{{ p.title }}</h4>
                <p class="ref-card__author">〔{{ p.dynasty }}〕{{ p.author }}</p>
                <div v-if="expandedRefId === p.id" class="ref-card__content">
                  <p v-for="(line, i) in p.content.split('\n').filter(Boolean)" :key="i" class="ref-card__line">{{ line }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="preview-panel">
        <div class="preview-card">
          <div class="preview-header">
            <span class="preview-badge">预览</span>
            <button type="button" class="preview-orient-btn" :class="{ 'preview-orient-btn--active': verticalPreview }" @click="verticalPreview = !verticalPreview" title="竖排/横排切换">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
              <span>{{ verticalPreview ? '横排' : '竖排' }}</span>
            </button>
          </div>
          <div class="scroll-body" :class="{ 'scroll-body--empty': !form.content, 'scroll-body--vertical': verticalPreview }">
            <template v-if="form.content">
              <h2 class="scroll-title">{{ form.title || '无题' }}</h2>
              <div class="scroll-genre">{{ genreLabel }}</div>
              <div class="scroll-divider"></div>
              <div class="scroll-content" :class="{ 'scroll-content--vertical': verticalPreview }">
                <p
                  v-for="(line, i) in contentLines"
                  :key="i"
                  class="scroll-line"
                  :style="{ animationDelay: `${i * 0.12}s` }"
                >{{ line }}</p>
              </div>
              <div class="scroll-author">— {{ authorName }}</div>
            </template>
            <template v-else>
              <div class="empty-state">
                <div class="empty-brush">筆</div>
                <p class="empty-text">落笔生花，此处将呈现你的作品</p>
                <div class="empty-actions">
                  <button type="button" class="empty-action empty-action--primary" @click="prepareAIGenerate(starterTopics[0])">AI 主题生成</button>
                  <button type="button" class="empty-action" @click="openReferencePanel">参考名篇</button>
                </div>
              </div>
            </template>
          </div>
        </div>
      </section>

      <aside class="ai-sidebar">
        <div class="ai-assistant-card">
          <div class="ai-assistant-card__header">
            <span class="ai-assistant-card__dot"></span>
            <span class="ai-assistant-card__title">翰林助手</span>
            <button v-if="aiChatHistory.length" class="ai-assistant-card__clear" @click="clearAIResult">&times;</button>
          </div>

          <div ref="aiChatScrollEl" class="ai-chat-scroll">
            <template v-for="(msg, idx) in aiChatHistory" :key="idx">
              <div class="ai-chat-msg" :class="`ai-chat-msg--${msg.role}`">
                <span class="ai-chat-msg__role">{{ msg.role === 'user' ? '我' : '翰林' }}</span>

                <template v-if="msg.role === 'user'">
                  <p class="ai-chat-msg__text">{{ msg.content }}</p>
                </template>

                <template v-else-if="msg.type === 'creation'">
                  <div class="ai-chat-msg__bubble">
                    <div class="ai-creation-content">{{ (msg.data as AICreationResponse)?.content }}</div>
                    <div v-if="(msg.data as AICreationResponse)?.explanation" class="ai-creation-explain">{{ (msg.data as AICreationResponse)?.explanation }}</div>
                    <div v-if="(msg.data as AICreationResponse)?.suggestions?.length" class="ai-creation-suggestions">
                      <div v-for="(s, i) in (msg.data as AICreationResponse)?.suggestions" :key="i" class="ai-suggestion-item">{{ s }}</div>
                    </div>
                    <div v-if="idx === aiChatHistory.length - 1 && aiResultType === 'creation'" class="ai-creation-actions">
                      <button class="ai-adopt-btn" @click="adoptAIContent('replace')">替换正文</button>
                      <button class="ai-append-btn" @click="adoptAIContent('append')">追加到正文</button>
                    </div>
                  </div>
                </template>

                <template v-else-if="msg.type === 'check'">
                  <div class="ai-chat-msg__bubble">
                    <div class="ai-check-summary" :class="(msg.data as AICheckPoemResponse)?.is_valid ? 'ai-check-summary--pass' : 'ai-check-summary--fail'">
                      <span class="ai-check-badge">{{ (msg.data as AICheckPoemResponse)?.is_valid ? '格律合规' : '格律有误' }}</span>
                      <span class="ai-check-detail">共发现 {{ (msg.data as AICheckPoemResponse)?.issues?.length || 0 }} 处问题</span>
                    </div>
                    <div v-if="(msg.data as AICheckPoemResponse)?.issues?.length" class="ai-issues-list">
                      <div v-for="(issue, i) in (msg.data as AICheckPoemResponse)?.issues" :key="i" class="ai-issue-item">
                        <span class="ai-issue-type">{{ issue.type }}</span>
                        <div class="ai-issue-body">
                          <div class="ai-issue-location">{{ issue.location }}</div>
                          <div class="ai-issue-desc">{{ issue.description }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="(msg.data as AICheckPoemResponse)?.suggestions?.length" class="ai-check-suggestions">
                      <div v-for="(s, i) in (msg.data as AICheckPoemResponse)?.suggestions" :key="i" class="ai-check-suggestion">{{ s }}</div>
                    </div>
                  </div>
                </template>

                <template v-else-if="msg.type === 'analyze'">
                  <div class="ai-chat-msg__bubble">
                    <div class="ai-score-grid">
                      <div class="ai-score-card ai-score-card--total">
                        <div class="ai-score-label">综合评分</div>
                        <div class="ai-score-value">{{ (msg.data as AIAnalyzePoemResponse)?.total_score || 0 }}</div>
                        <div class="ai-score-bar"><div class="ai-score-bar__fill" :style="{ width: ((msg.data as AIAnalyzePoemResponse)?.total_score || 0) + '%' }"></div></div>
                      </div>
                      <div class="ai-score-card">
                        <div class="ai-score-label">格律</div>
                        <div class="ai-score-value">{{ (msg.data as AIAnalyzePoemResponse)?.meter_score || 0 }}</div>
                        <div class="ai-score-bar"><div class="ai-score-bar__fill" :style="{ width: (((msg.data as AIAnalyzePoemResponse)?.meter_score || 0) * 4) + '%' }"></div></div>
                      </div>
                      <div class="ai-score-card">
                        <div class="ai-score-label">意境</div>
                        <div class="ai-score-value">{{ (msg.data as AIAnalyzePoemResponse)?.artistic_score || 0 }}</div>
                        <div class="ai-score-bar"><div class="ai-score-bar__fill" :style="{ width: (((msg.data as AIAnalyzePoemResponse)?.artistic_score || 0) * 4) + '%' }"></div></div>
                      </div>
                      <div class="ai-score-card">
                        <div class="ai-score-label">用词</div>
                        <div class="ai-score-value">{{ (msg.data as AIAnalyzePoemResponse)?.diction_score || 0 }}</div>
                        <div class="ai-score-bar"><div class="ai-score-bar__fill" :style="{ width: (((msg.data as AIAnalyzePoemResponse)?.diction_score || 0) * 4) + '%' }"></div></div>
                      </div>
                      <div class="ai-score-card">
                        <div class="ai-score-label">综合</div>
                        <div class="ai-score-value">{{ (msg.data as AIAnalyzePoemResponse)?.overall_score || 0 }}</div>
                        <div class="ai-score-bar"><div class="ai-score-bar__fill" :style="{ width: (((msg.data as AIAnalyzePoemResponse)?.overall_score || 0) * 4) + '%' }"></div></div>
                      </div>
                    </div>
                    <div v-if="(msg.data as AIAnalyzePoemResponse)?.highlights?.length" class="ai-highlights">
                      <div class="ai-section-title">亮点</div>
                      <div class="ai-highlight-list">
                        <div v-for="(h, i) in (msg.data as AIAnalyzePoemResponse)?.highlights" :key="i" class="ai-highlight-item">{{ h }}</div>
                      </div>
                    </div>
                    <div v-if="(msg.data as AIAnalyzePoemResponse)?.improvements?.length" class="ai-improvements">
                      <div class="ai-section-title">改进建议</div>
                      <div class="ai-highlight-list">
                        <div v-for="(m, i) in (msg.data as AIAnalyzePoemResponse)?.improvements" :key="i" class="ai-improvement-item">{{ m }}</div>
                      </div>
                    </div>
                    <div v-if="(msg.data as AIAnalyzePoemResponse)?.appreciation" class="ai-appreciation">{{ (msg.data as AIAnalyzePoemResponse)?.appreciation }}</div>
                  </div>
                </template>

                <template v-else>
                  <p class="ai-chat-msg__text">{{ msg.content }}</p>
                </template>
              </div>
            </template>

            <div v-if="aiLoading" class="ai-chat-msg ai-chat-msg--assistant">
              <span class="ai-chat-msg__role">翰林</span>
              <div class="ai-chat-msg__bubble">
                <div class="ai-result__loading">
                  <div class="ai-loading-ink">
                    <div class="ai-loading-ink__drop"></div>
                    <div class="ai-loading-ink__ripple"></div>
                    <div class="ai-loading-ink__ripple ai-loading-ink__ripple--delay"></div>
                  </div>
                  <span class="ai-loading-text">{{ aiLoadingText }}</span>
                  <div v-if="aiMode === 'check' && aiProgressSteps.length" class="ai-progress-steps">
                    <div v-for="(step, idx) in aiProgressSteps" :key="idx" class="ai-progress-step" :class="{ active: idx === aiCurrentStep }">
                      {{ step }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="!aiChatHistory.length && !aiLoading" class="ai-empty">
              <div class="ai-empty__glyph">翰</div>
              <p class="ai-empty__text">点击工具栏按钮开始对话</p>
              <p class="ai-empty__hint">续写 · 灵感 · 生成 · 格律 · 评分</p>
              <div class="ai-sidebar-topics">
                <button
                  v-for="topic in starterTopics"
                  :key="topic"
                  type="button"
                  class="ai-sidebar-topic"
                  @click="applyStarterTopic(topic); prepareAIGenerate(topic)"
                >{{ topic }}</button>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <AppToast v-model="toast.show" :message="toast.message" :type="toast.type" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { worksApi } from '@/api/works'
import { poemApi, type Poem } from '@/api/poem'
import { useUserStore } from '@/store/modules/user'
import {
  aiCheckPoemStream,
  aiAnalyzePoemStream,
  aiCreationStream,
  type AICreationResponse,
  type AICheckPoemResponse,
  type AIAnalyzePoemResponse,
  type StreamEvent,
} from '@/api/ai'
import AppToast from '@/components/AppToast.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const genres = [
  { value: '五言绝句', label: '五言绝句', glyph: '绝', hint: '每句五字，共四句' },
  { value: '七言绝句', label: '七言绝句', glyph: '绝', hint: '每句七字，共四句' },
  { value: '五言律诗', label: '五言律诗', glyph: '律', hint: '每句五字，共八句' },
  { value: '七言律诗', label: '七言律诗', glyph: '律', hint: '每句七字，共八句' },
  { value: '词', label: '词', glyph: '词', hint: '依词牌填写' },
  { value: '自由体', label: '自由体', glyph: '自', hint: '不拘格律，自由创作' },
]

const starterTopicMap: Record<string, string[]> = {
  '五言绝句': ['春夜', '山行', '雨后'],
  '七言绝句': ['明月', '江风', '归途'],
  '五言律诗': ['书斋', '秋声', '夜坐'],
  '七言律诗': ['登临', '怀古', '远行'],
  '词': ['新晴', '小楼', '相思'],
  '自由体': ['少年心事', '风过长街', '灯下所感'],
}

const form = ref({
  title: '',
  content: '',
  genre: '七言绝句'
})

const saving = ref(false)
const publishing = ref(false)
const editingId = ref<number | null>(null)
const lastSavedAt = ref<string>('')
const hasUnsavedChanges = ref(false)
const autoSaveTimer = ref<ReturnType<typeof setInterval> | null>(null)
const formSnapshot = ref('')

const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' | 'warning' | 'info' })

const refOpen = ref(false)
const refSearchInputEl = ref<HTMLInputElement | null>(null)
const refPoem = ref<{ title: string; author: string; dynasty: string; content: string } | null>(null)
const refQuery = ref('')
const refSearching = ref(false)
const refResults = ref<Poem[]>([])
const expandedRefId = ref<number | null>(null)

const isImitateMode = ref(false)
const imitatePoem = ref<{ id: number; title: string; author: string; dynasty: string; content: string; genre?: string; category?: string } | null>(null)
const imitateRefId = ref<number | null>(null)

const imitatePoemLines = computed(() => {
  if (!imitatePoem.value) return []
  return imitatePoem.value.content.split('\n').filter((l: string) => l.trim())
})

const imitateStructDesc = computed(() => {
  const lines = imitatePoemLines.value
  if (!lines.length) return ''
  const charCounts = lines.map((l: string) => l.replace(/[\uff0c\u3002\uff01\uff1f\uff1b\u3001\s]/g, '').length)
  const avgChars = Math.round(charCounts.reduce((a: number, b: number) => a + b, 0) / charCounts.length)
  const firstCount = charCounts[0]!
  const allSame = charCounts.every((c: number) => c === firstCount)
  if (allSame) {
    return `${lines.length}\u884c\u00d7\u6bcf\u884c${firstCount}\u5b57`
  }
  return `${lines.length}\u884c\uff0c\u5e73\u5747\u6bcf\u884c${avgChars}\u5b57`
})

function inferGenreFromPoem(content: string, originalGenre?: string): string {
  const validGenres = genres.map(g => g.value)
  if (originalGenre && validGenres.includes(originalGenre)) return originalGenre

  const lines = content.split('\n').filter(l => l.trim())
  const charCounts = lines.map(l => l.replace(/[\s，。！？；、：""''（）]/g, '').length)
  const lineCount = lines.length
  const avgChars = charCounts.length ? Math.round(charCounts.reduce((a, b) => a + b, 0) / charCounts.length) : 0
  const allSameLength = charCounts.length > 0 && charCounts.every(c => c === charCounts[0])

  if (originalGenre === '词' || (!allSameLength && lineCount >= 4)) return '词'
  if (allSameLength && avgChars === 5 && lineCount === 4) return '五言绝句'
  if (allSameLength && avgChars === 7 && lineCount === 4) return '七言绝句'
  if (allSameLength && avgChars === 5 && lineCount === 8) return '五言律诗'
  if (allSameLength && avgChars === 7 && lineCount === 8) return '七言律诗'

  return '自由体'
}

function buildImitateTemplate(content: string): string {
  return content
    .split('\n')
    .map(line => line.replace(/[^\s，。！？；、：""''（）\n]/g, '○'))
    .join('\n')
}

function applyImitateTemplate() {
  if (!imitatePoem.value) return
  const template = buildImitateTemplate(imitatePoem.value.content)
  form.value.content = template
  showToast('\u5df2\u8f7d\u5165\u4eff\u5199\u9aa8\u67b6\uff0c\u8bf7\u5c06\u25cb\u66ff\u6362\u4e3a\u4f60\u7684\u8bd7\u53e5', 'info')
}

function viewFullRef() {
  if (!imitatePoem.value) return
  refPoem.value = {
    title: imitatePoem.value.title,
    author: imitatePoem.value.author,
    dynasty: imitatePoem.value.dynasty,
    content: imitatePoem.value.content
  }
  refOpen.value = true
}

function exitImitateMode() {
  isImitateMode.value = false
  imitatePoem.value = null
  imitateRefId.value = null
}

function goBack() {
  if (imitateRefId.value) {
    router.push(`/poems/${imitateRefId.value}`)
    return
  }
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/works')
  }
}

type AIMode = 'continue' | 'inspire' | 'generate' | 'check' | 'analyze' | 'imitate_guide' | null
type AIResultType = 'creation' | 'check' | 'analyze' | null

const aiMode = ref<AIMode>(null)
const aiLoading = ref(false)
const aiError = ref('')
const aiResultType = ref<AIResultType>(null)
const aiPanelOpen = ref(true)
const verticalPreview = ref(false)
const textareaFlash = ref(false)
const showGenerateInput = ref(false)
const aiKeywords = ref('')
const aiProgressSteps = ref<string[]>([])
const aiCurrentStep = ref(0)
const aiCreationResult = ref<AICreationResponse | null>(null)
const aiCheckResult = ref<AICheckPoemResponse | null>(null)
const aiAnalyzeResult = ref<AIAnalyzePoemResponse | null>(null)
const lastAIMode = ref<AIMode>(null)

interface AIChatMessage {
  role: 'user' | 'assistant'
  type: AIResultType | 'text'
  content: string
  data?: AICreationResponse | AICheckPoemResponse | AIAnalyzePoemResponse | null
}
const aiChatHistory = ref<AIChatMessage[]>([])

const aiLoadingText = ref('思考中…')

const _defaultLoadingText: Record<string, string> = {
  continue: '正在续写中…',
  inspire: '正在构思灵感…',
  generate: '正在生成诗词…',
  check: '正在检查格律…',
  analyze: '正在赏析评分…',
  imitate_guide: '正在分析原诗风格…',
}

function handleStreamEvent(event: StreamEvent) {
  if (event.type === 'thinking' && event.content) {
    aiLoadingText.value = event.content
  } else if (event.type === 'tool_call') {
    const labels = (event as any).labels as string[] | undefined
    const names = labels?.length ? labels.join('、') : (event.tools?.join('、') || '')
    aiLoadingText.value = names ? `正在${names}…` : '正在调用工具…'
  }
  scrollChatToBottom()
}

const aiChatScrollEl = ref<HTMLElement | null>(null)

function scrollChatToBottom() {
  nextTick(() => {
    if (aiChatScrollEl.value) {
      aiChatScrollEl.value.scrollTop = aiChatScrollEl.value.scrollHeight
    }
  })
}

const userMsgMap: Record<string, (ctx: string) => string> = {
  continue: (ctx) => `请帮我续写：${ctx.slice(0, 40)}…`,
  inspire: (ctx) => `请给我关于「${ctx.slice(0, 20)}」的灵感建议`,
  generate: (ctx) => `请以「${ctx}」为主题生成一首诗`,
  check: () => '请检查这首诗的格律',
  analyze: () => '请赏析并评分这首诗',
  imitate_guide: () => '请分析原诗风格，给出仿写指导',
}

async function triggerAI(mode: string) {
  if (aiLoading.value) return

  if (mode === 'generate' && !showGenerateInput.value) {
    showGenerateInput.value = true
    aiMode.value = 'generate'
    return
  }

  aiMode.value = mode as AIMode
  lastAIMode.value = mode as AIMode
  aiLoading.value = true
  aiError.value = ''
  aiPanelOpen.value = true
  aiLoadingText.value = _defaultLoadingText[mode] || '思考中…'
  aiCreationResult.value = null
  aiCheckResult.value = null
  aiAnalyzeResult.value = null
  aiResultType.value = null

  const ctx = mode === 'generate'
    ? (aiKeywords.value.trim() || '古典诗词')
    : (form.value.content.trim() || form.value.title.trim() || form.value.genre)
  const msgFn = userMsgMap[mode]
  if (msgFn) {
    aiChatHistory.value.push({ role: 'user', type: 'text', content: msgFn(ctx) })
    scrollChatToBottom()
  }

  if (mode === 'check') {
    aiProgressSteps.value = ['验证诗句', '检查格律', '分析平仄', '生成报告']
    aiCurrentStep.value = 0

    try {
      await aiCheckPoemStream(
        { poem_text: form.value.content.trim() },
        (event: StreamEvent) => {
          handleStreamEvent(event)
          if (aiCurrentStep.value < aiProgressSteps.value.length - 1) {
            aiCurrentStep.value++
          }
        },
        (result: AICheckPoemResponse) => {
          aiCheckResult.value = result
          aiResultType.value = 'check'
          aiChatHistory.value.push({ role: 'assistant', type: 'check', content: '', data: result })
          scrollChatToBottom()
        },
        (err: string) => {
          aiError.value = err
          aiChatHistory.value.push({ role: 'assistant', type: 'text', content: err })
          scrollChatToBottom()
        },
      )
    } catch (e: any) {
      aiError.value = e?.response?.data?.detail || 'AI服务暂时不可用，请稍后重试'
    } finally {
      aiLoading.value = false
      aiProgressSteps.value = []
      aiCurrentStep.value = 0
    }
    return
  }

  const refPoemPayload = isImitateMode.value && imitatePoem.value
    ? {
        title: imitatePoem.value.title,
        author: imitatePoem.value.author,
        dynasty: imitatePoem.value.dynasty,
        content: imitatePoem.value.content,
        genre: imitatePoem.value.genre,
      }
    : undefined

  try {
    if (mode === 'imitate_guide') {
      await aiCreationStream(
        { context: imitatePoem.value?.title || '仿写', mode: 'imitate_guide', reference_poem: refPoemPayload },
        handleStreamEvent,
        (result: AICreationResponse) => {
          aiCreationResult.value = result; aiResultType.value = 'creation'
          aiChatHistory.value.push({ role: 'assistant', type: 'creation', content: '', data: result })
          scrollChatToBottom()
        },
        (err: string) => {
          aiError.value = err
          aiChatHistory.value.push({ role: 'assistant', type: 'text', content: err })
          scrollChatToBottom()
        },
      )
    } else if (mode === 'continue' || mode === 'inspire' || mode === 'generate') {
      const context = mode === 'generate'
        ? (aiKeywords.value.trim() || '古典诗词')
        : (form.value.content.trim() || form.value.title.trim() || form.value.genre)
      const keywords = mode === 'generate' && aiKeywords.value.trim()
        ? aiKeywords.value.split(/[,，、\s]+/).filter(Boolean)
        : undefined
      await aiCreationStream(
        { context, mode: mode === 'generate' ? 'theme' : mode as 'continue' | 'inspire', keywords, reference_poem: refPoemPayload },
        handleStreamEvent,
        (result: AICreationResponse) => {
          aiCreationResult.value = result; aiResultType.value = 'creation'
          aiChatHistory.value.push({ role: 'assistant', type: 'creation', content: '', data: result })
          scrollChatToBottom()
        },
        (err: string) => {
          aiError.value = err
          aiChatHistory.value.push({ role: 'assistant', type: 'text', content: err })
          scrollChatToBottom()
        },
      )
    } else if (mode === 'analyze') {
      await aiAnalyzePoemStream(
        { poem_text: form.value.content.trim() },
        handleStreamEvent,
        (result: AIAnalyzePoemResponse) => {
          aiAnalyzeResult.value = result; aiResultType.value = 'analyze'
          aiChatHistory.value.push({ role: 'assistant', type: 'analyze', content: '', data: result })
          scrollChatToBottom()
        },
        (err: string) => {
          aiError.value = err
          aiChatHistory.value.push({ role: 'assistant', type: 'text', content: err })
          scrollChatToBottom()
        },
      )
    }
  } catch (e: any) {
    aiError.value = e?.response?.data?.detail || 'AI服务暂时不可用，请稍后重试'
  } finally {
    aiLoading.value = false
  }
}

function clearAIResult() {
  aiResultType.value = null
  aiCreationResult.value = null
  aiCheckResult.value = null
  aiAnalyzeResult.value = null
  aiError.value = ''
  aiMode.value = null
  aiPanelOpen.value = false
  aiChatHistory.value = []
}

function adoptAIContent(action: 'replace' | 'append') {
  if (!aiCreationResult.value?.content) return
  if (action === 'replace') {
    form.value.content = aiCreationResult.value.content
  } else {
    const sep = form.value.content.trim() ? '\n' : ''
    form.value.content = form.value.content.trim() + sep + aiCreationResult.value.content
  }
  textareaFlash.value = true
  setTimeout(() => { textareaFlash.value = false }, 600)
  showToast('已采纳 AI 内容')
}

const authorName = computed(() =>
  userStore.userInfo?.nickname || userStore.userInfo?.username || '佚名'
)

const canPublish = computed(() =>
  form.value.title.trim().length > 0 &&
  form.value.content.trim().length > 0 &&
  form.value.genre.length > 0
)

const contentLines = computed(() =>
  form.value.content
    .split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0)
)

const genreLabel = computed(() => {
  const g = genres.find(g => g.value === form.value.genre)
  return g?.label || ''
})

const contentHint = computed(() => {
  const g = genres.find(g => g.value === form.value.genre)
  return g?.hint || ''
})

const currentPlaceholder = computed(() => {
  const map: Record<string, string> = {
    '五言绝句': '白日依山尽\n黄河入海流\n欲穷千里目\n更上一层楼',
    '七言绝句': '两个黄鹂鸣翠柳\n一行白鹭上青天\n窗含西岭千秋雪\n门泊东吴万里船',
    '五言律诗': '国破山河在\n城春草木深\n感时花溅泪\n恨别鸟惊心\n烽火连三月\n家书抵万金\n白头搔更短\n浑欲不胜簪',
    '七言律诗': '风急天高猿啸哀\n渚清沙白鸟飞回\n无边落木萧萧下\n不尽长江滚滚来\n万里悲秋常作客\n百年多病独登台\n艰难苦恨繁霜鬓\n潦倒新停浊酒杯',
    '词': '明月几时有\n把酒问青天\n不知天上宫阙\n今夕是何年',
    '自由体': '在此自由书写你的诗篇...',
  }
  return map[form.value.genre] || '在此书写你的诗篇...'
})

const showStarterGuide = computed(() =>
  !editingId.value &&
  !form.value.title.trim() &&
  !form.value.content.trim()
)

const starterTopics = computed(() => {
  return starterTopicMap[form.value.genre] || starterTopicMap['自由体'] || []
})

function showToast(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'success') {
  toast.value = { show: true, message, type }
}

function onContentInput() {
  hasUnsavedChanges.value = JSON.stringify(form.value) !== formSnapshot.value
}

function markSaved() {
  formSnapshot.value = JSON.stringify(form.value)
  hasUnsavedChanges.value = false
  const now = new Date()
  lastSavedAt.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

async function autoSave() {
  if (!hasUnsavedChanges.value) return
  if (saving.value || publishing.value) return
  if (!form.value.title.trim() && !form.value.content.trim()) return
  saving.value = true
  try {
    if (editingId.value) {
      await worksApi.updateWork(editingId.value, {
        title: form.value.title,
        content: form.value.content,
        genre: form.value.genre
      })
    } else {
      const res = await worksApi.createWork({
        title: form.value.title || '无题',
        content: form.value.content || ' ',
        genre: form.value.genre
      })
      editingId.value = res.id
    }
    markSaved()
  } catch {}
  finally {
    saving.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveDraft()
  }
}

function handleBeforeUnload(e: BeforeUnloadEvent) {
  if (hasUnsavedChanges.value) {
    e.preventDefault()
  }
}

const contentLineCount = computed(() => {
  if (!form.value.content.trim()) return 0
  return form.value.content.split('\n').filter(l => l.trim()).length
})

const expectedLineCount = computed(() => {
  const map: Record<string, number> = {
    '五言绝句': 4,
    '七言绝句': 4,
    '五言律诗': 8,
    '七言律诗': 8,
  }
  return map[form.value.genre] || 0
})

const lineCountStatus = computed(() => {
  if (!expectedLineCount.value || !contentLineCount.value) return ''
  if (contentLineCount.value === expectedLineCount.value) return 'match'
  if (contentLineCount.value > expectedLineCount.value) return 'over'
  return 'under'
})

function prepareAIGenerate(topic?: string) {
  aiMode.value = 'generate'
  lastAIMode.value = 'generate'
  aiPanelOpen.value = true
  showGenerateInput.value = true

  if (topic) {
    aiKeywords.value = topic

    if (!form.value.title.trim()) {
      form.value.title = topic
    }
  }
}

function openReferencePanel() {
  refOpen.value = true

  if (!refQuery.value.trim()) {
    refQuery.value = form.value.title.trim() || starterTopics.value[0] || form.value.genre
  }

  nextTick(() => {
    refSearchInputEl.value?.focus()
    refSearchInputEl.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })

    if (refQuery.value.trim() && !refResults.value.length) {
      searchRefPoems()
    }
  })
}

function applyStarterTopic(topic: string) {
  if (!form.value.title.trim()) {
    form.value.title = topic
  }

  aiKeywords.value = topic
  showToast(`已填入题眼「${topic}」`, 'info')
}

async function saveDraft() {
  if (!form.value.title.trim() && !form.value.content.trim()) {
    showToast('请至少填写标题或正文', 'warning')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await worksApi.updateWork(editingId.value, {
        title: form.value.title,
        content: form.value.content,
        genre: form.value.genre
      })
      showToast('草稿已更新')
    } else {
      const res = await worksApi.createWork({
        title: form.value.title || '无题',
        content: form.value.content || ' ',
        genre: form.value.genre
      })
      editingId.value = res.id
      showToast('草稿已保存')
    }
    markSaved()
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function publishWork() {
  if (!canPublish.value) return
  publishing.value = true
  try {
    if (!editingId.value) {
      const res = await worksApi.createWork({
        title: form.value.title,
        content: form.value.content,
        genre: form.value.genre
      })
      editingId.value = res.id
    } else {
      await worksApi.updateWork(editingId.value, {
        title: form.value.title,
        content: form.value.content,
        genre: form.value.genre
      })
    }
    await worksApi.publishWork(editingId.value!)
    await userStore.fetchUserInfo()
    showToast('作品发布成功，等级经验已同步')
    setTimeout(() => router.push(`/works/${editingId.value}`), 1200)
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '发布失败', 'error')
  } finally {
    publishing.value = false
  }
}

async function searchRefPoems() {
  const q = refQuery.value.trim()
  if (!q) return
  refSearching.value = true
  try {
    const res = await poemApi.search({ keyword: q, page: 1, page_size: 8 })
    refResults.value = res.items
  } catch {
    refResults.value = []
  } finally {
    refSearching.value = false
  }
}

onMounted(async () => {
  const id = route.query.id
  if (id) {
    try {
      const work = await worksApi.getWorkDetail(Number(id))
      editingId.value = work.id
      form.value.title = work.title
      form.value.content = work.content
      form.value.genre = work.genre
    } catch {}
  }

  const mode = route.query.mode as string
  const refId = route.query.ref_id as string
  const refTitle = route.query.ref_title as string
  const refAuthor = route.query.ref_author as string
  const refDynasty = route.query.ref_dynasty as string
  const refGenre = route.query.ref_genre as string

  if (mode === 'imitate' && refId) {
    imitateRefId.value = Number(refId)
    try {
      const detail = await poemApi.getDetail(Number(refId))
      imitatePoem.value = {
        id: detail.id,
        title: detail.title,
        author: detail.author,
        dynasty: detail.dynasty,
        content: detail.content,
        genre: detail.genre,
        category: detail.category,
      }
      isImitateMode.value = true
      refPoem.value = { title: detail.title, author: detail.author, dynasty: detail.dynasty, content: detail.content }
      refOpen.value = true
      const matchedGenre = inferGenreFromPoem(detail.content, detail.genre)
      form.value.genre = matchedGenre
    } catch {
      if (refTitle && refAuthor) {
        refPoem.value = { title: refTitle, author: refAuthor, dynasty: refDynasty || '', content: '' }
        refOpen.value = true
      }
      if (refGenre) {
        const matchGenre = genres.find(g => g.value === refGenre)
        if (matchGenre) form.value.genre = matchGenre.value
      }
    }
  } else if (refTitle && refAuthor) {
    refOpen.value = true
    try {
      const res = await poemApi.search({ keyword: refTitle, search_type: 'title', page: 1, page_size: 1 })
      const p = res.items[0]
      if (p) {
        refPoem.value = { title: p.title, author: p.author, dynasty: p.dynasty, content: p.content }
      } else {
        refPoem.value = { title: refTitle, author: refAuthor, dynasty: refDynasty || '', content: '' }
      }
    } catch {
      refPoem.value = { title: refTitle, author: refAuthor, dynasty: refDynasty || '', content: '' }
    }
    if (refGenre) {
      const matchGenre = genres.find(g => g.value === refGenre)
      if (matchGenre) form.value.genre = matchGenre.value
    }
  }

  formSnapshot.value = JSON.stringify(form.value)

  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('beforeunload', handleBeforeUnload)

  autoSaveTimer.value = setInterval(autoSave, 60000)
})

watch(() => form.value.title, () => {
  hasUnsavedChanges.value = JSON.stringify(form.value) !== formSnapshot.value
})

watch(() => form.value.genre, () => {
  hasUnsavedChanges.value = JSON.stringify(form.value) !== formSnapshot.value
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value)
  }
})
</script>

<style scoped>
@import './styles/ai-assistant.css';
.create-page {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(170deg, #f6f1e8 0%, #fdfefe 40%, #f0ebe2 100%);
  overflow: hidden;
}

.ink-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.ink-wash {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.18;
}

.ink-wash--1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -100px;
  background: radial-gradient(circle, rgba(192,57,43,0.3), transparent 70%);
}

.ink-wash--2 {
  width: 500px;
  height: 500px;
  bottom: -150px;
  left: -80px;
  background: radial-gradient(circle, rgba(22,160,133,0.25), transparent 70%);
}

.create-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 32px;
  background: rgba(253,254,254,0.88);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(44,62,80,0.06);
}

.nav-back {
  font-size: 0.92rem;
  color: var(--color-ink-medium);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.nav-back:hover {
  color: var(--color-vermilion);
}

.nav-title {
  font-family: var(--font-poem);
  font-size: 1.2rem;
  letter-spacing: 0.2em;
  color: var(--color-ink-dark);
}

.nav-actions {
  display: flex;
  gap: 10px;
}

.btn-save,
.btn-publish {
  height: 36px;
  padding: 0 20px;
  border-radius: 999px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.btn-save {
  background: rgba(44,62,80,0.08);
  color: var(--color-ink-medium);
}

.btn-save:hover:not(:disabled) {
  background: rgba(44,62,80,0.14);
}

.btn-publish {
  background: linear-gradient(135deg, var(--color-vermilion), #b73325);
  color: #fff;
  box-shadow: 0 4px 14px rgba(192,57,43,0.2);
}

.btn-publish:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(192,57,43,0.28);
}

.btn-save:disabled,
.btn-publish:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.create-body {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 24px;
  max-width: 1560px;
  margin: 0 auto;
  padding: 32px;
  min-height: calc(100vh - 60px);
}

.editor-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.editor-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 32px;
  border-radius: 24px;
  background: rgba(255,255,255,0.82);
  border: 1px solid rgba(44,62,80,0.07);
  box-shadow: 0 20px 50px rgba(44,62,80,0.08);
  backdrop-filter: blur(10px);
  min-height: 600px;
  overflow: hidden;
}

.editor-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-vermilion), var(--color-gold, #b28d57), transparent);
  border-radius: 24px 24px 0 0;
}

.card-seal {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(192,57,43,0.2);
  color: rgba(192,57,43,0.8);
  border-radius: 14px;
  font-family: var(--font-poem);
  font-size: 1.3rem;
  letter-spacing: 0.15em;
  background: rgba(255,247,244,0.7);
  transform: rotate(8deg);
}

.field-group {
  margin-bottom: 24px;
}

.field-group--grow {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.field-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--color-ink-dark);
  letter-spacing: 0.06em;
}

.field-hint {
  font-weight: 400;
  font-size: 0.82rem;
  color: rgba(52,73,94,0.6);
}

.field-input {
  width: 100%;
  height: 48px;
  padding: 0 18px;
  border: 1px solid rgba(44,62,80,0.12);
  border-radius: 14px;
  font-size: 1rem;
  font-family: var(--font-poem);
  color: var(--color-ink-dark);
  background: rgba(255,255,255,0.6);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  outline: none;
}

.field-input:focus {
  border-color: var(--color-vermilion);
  box-shadow: 0 0 0 3px rgba(192,57,43,0.08);
}

.field-input::placeholder {
  color: rgba(52,73,94,0.35);
}

.genre-grid {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding-bottom: 2px;
}

.genre-grid::-webkit-scrollbar {
  display: none;
}

.starter-guide {
  margin-bottom: 24px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(44,62,80,0.08);
  background:
    linear-gradient(135deg, rgba(255,247,244,0.86), rgba(255,255,255,0.76));
  box-shadow: 0 14px 28px rgba(44,62,80,0.06);
}

.starter-guide__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.starter-guide__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(192,57,43,0.1);
  color: var(--color-vermilion);
  font-size: 0.74rem;
  letter-spacing: 0.12em;
}

.starter-guide__note {
  font-size: 0.8rem;
  color: rgba(52,73,94,0.56);
}

.starter-guide__text {
  margin-top: 10px;
  font-size: 0.88rem;
  line-height: 1.8;
  color: rgba(52,73,94,0.7);
}

.starter-guide__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.starter-guide__action {
  min-height: 36px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(44,62,80,0.1);
  background: rgba(255,255,255,0.72);
  color: var(--color-ink-dark);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.starter-guide__action:hover {
  transform: translateY(-1px);
  border-color: rgba(192,57,43,0.16);
  color: var(--color-vermilion);
}

.starter-guide__action--primary {
  border-color: transparent;
  background: linear-gradient(135deg, var(--color-vermilion), #b73325);
  color: #fff;
  box-shadow: 0 8px 18px rgba(192,57,43,0.18);
}

.starter-guide__action--primary:hover {
  color: #fff;
  box-shadow: 0 12px 22px rgba(192,57,43,0.24);
}

.starter-guide__topics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.starter-guide__topic {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px dashed rgba(44,62,80,0.14);
  background: rgba(255,255,255,0.68);
  color: rgba(52,73,94,0.7);
  font-size: 0.78rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.starter-guide__topic:hover {
  border-color: rgba(192,57,43,0.2);
  color: var(--color-vermilion);
  background: rgba(255,247,244,0.8);
}

.genre-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 14px;
  border: 1px solid rgba(44,62,80,0.1);
  background: rgba(255,255,255,0.5);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  flex-shrink: 0;
}

.genre-chip:hover {
  border-color: rgba(192,57,43,0.2);
  background: rgba(255,247,244,0.6);
}

.genre-chip--active {
  border-color: var(--color-vermilion);
  background: rgba(192,57,43,0.06);
  box-shadow: 0 2px 10px rgba(192,57,43,0.1);
}

.genre-chip--active .genre-glyph {
  color: var(--color-vermilion);
  background: rgba(192,57,43,0.12);
}

.genre-glyph {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-family: var(--font-poem);
  font-size: 0.95rem;
  color: var(--color-ink-medium);
  background: rgba(44,62,80,0.06);
  transition: all var(--transition-fast);
}

.genre-name {
  font-size: 0.88rem;
  color: var(--color-ink-dark);
}

.field-textarea {
  flex: 1;
  width: 100%;
  min-height: 240px;
  padding: 18px;
  border: 1px solid rgba(44,62,80,0.12);
  border-radius: 14px;
  font-family: var(--font-poem);
  font-size: 1.1rem;
  line-height: 2.2;
  color: var(--color-ink-dark);
  background: rgba(255,255,255,0.6);
  resize: none;
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.field-textarea:focus {
  border-color: var(--color-vermilion);
  box-shadow: -3px 0 0 0 var(--color-vermilion), 0 0 0 3px rgba(192,57,43,0.08);
}

.field-textarea--flash {
  animation: textareaFlash 0.6s ease;
}

@keyframes textareaFlash {
  0% { background: rgba(255,255,255,0.6); }
  30% { background: rgba(178,141,87,0.12); }
  100% { background: rgba(255,255,255,0.6); }
}

.field-textarea::-webkit-scrollbar {
  width: 6px;
}

.field-textarea::-webkit-scrollbar-track {
  background: transparent;
}

.field-textarea::-webkit-scrollbar-thumb {
  background: rgba(44,62,80,0.15);
  border-radius: 3px;
  transition: background 0.3s;
}

.field-textarea::-webkit-scrollbar-thumb:hover {
  background: rgba(192,57,43,0.3);
}

.field-textarea {
  scrollbar-width: thin;
  scrollbar-color: rgba(44,62,80,0.15) transparent;
}

.field-textarea::placeholder {
  color: rgba(52,73,94,0.3);
  font-style: italic;
}

.textarea-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.auto-save-hint {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.78rem;
  color: rgba(52,73,94,0.45);
  transition: color 0.3s;
}

.auto-save-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4caf50;
  flex-shrink: 0;
  transition: background 0.3s;
}

.auto-save-dot--unsaved {
  background: #f0a020;
  animation: auto-save-pulse 1.5s ease-in-out infinite;
}

@keyframes auto-save-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.char-count {
  display: inline-flex;
  align-items: center;
  gap: 0;
  font-size: 0.82rem;
  color: rgba(52,73,94,0.5);
}

.line-count {
  font-weight: 600;
  transition: color 0.3s;
}

.line-count--match {
  color: #4caf50;
}

.line-count--under {
  color: rgba(52,73,94,0.5);
}

.line-count--over {
  color: #e57373;
}

.count-sep {
  margin: 0 5px;
  color: rgba(52,73,94,0.25);
}

.preview-panel {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
}

.preview-card {
  position: sticky;
  top: 92px;
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  overflow: hidden;
  background:
    radial-gradient(ellipse at top left, rgba(246,241,232,0.95), transparent 60%),
    linear-gradient(180deg, rgba(253,249,240,0.98), rgba(246,241,232,0.98));
  border: 1px solid rgba(44,62,80,0.07);
  box-shadow: 0 20px 50px rgba(44,62,80,0.08);
  min-height: 400px;
  max-height: calc(100vh - 124px);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(44,62,80,0.06);
}

.preview-orient-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(44,62,80,0.1);
  background: rgba(255,255,255,0.6);
  color: rgba(52,73,94,0.6);
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.preview-orient-btn:hover {
  border-color: rgba(192,57,43,0.2);
  color: var(--color-vermilion);
  background: rgba(255,247,244,0.8);
}

.preview-orient-btn--active {
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
  background: rgba(192,57,43,0.06);
}

.preview-badge {
  font-size: 0.82rem;
  letter-spacing: 0.18em;
  color: rgba(52,73,94,0.6);
}

.scroll-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  text-align: center;
}

.scroll-body--empty {
  opacity: 0.6;
}

.scroll-title {
  font-family: var(--font-title);
  font-size: 1.8rem;
  color: var(--color-ink-dark);
  margin-bottom: 8px;
  letter-spacing: 0.08em;
}

.scroll-genre {
  font-size: 0.85rem;
  color: rgba(52,73,94,0.55);
  margin-bottom: 16px;
  letter-spacing: 0.12em;
}

.scroll-divider {
  width: 48px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-vermilion), transparent);
  margin-bottom: 28px;
  opacity: 0.5;
}

.scroll-content {
  margin-bottom: 28px;
}

.scroll-line {
  font-family: var(--font-poem);
  font-size: 1.25rem;
  line-height: 2.4;
  color: var(--color-ink-dark);
  letter-spacing: 0.15em;
  animation: lineReveal 0.6s ease both;
}

@keyframes lineReveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.scroll-author {
  font-size: 0.95rem;
  color: rgba(52,73,94,0.6);
  font-family: var(--font-poem);
  letter-spacing: 0.1em;
}

.scroll-body--vertical {
  direction: rtl;
}

.scroll-body--vertical .scroll-title,
.scroll-body--vertical .scroll-genre,
.scroll-body--vertical .scroll-author {
  direction: ltr;
}

.scroll-content--vertical {
  writing-mode: vertical-rl;
  direction: ltr;
  text-align: start;
  max-height: 360px;
  overflow-x: auto;
  padding: 8px 0;
}

.scroll-content--vertical .scroll-line {
  line-height: 2;
  letter-spacing: 0.2em;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-brush {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(44,62,80,0.04);
  font-family: var(--font-poem);
  font-size: 2rem;
  color: rgba(44,62,80,0.18);
}

.empty-text {
  font-size: 0.92rem;
  color: rgba(52,73,94,0.45);
  line-height: 1.6;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 4px;
}

.empty-action {
  min-height: 36px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(44,62,80,0.12);
  background: rgba(255,255,255,0.76);
  color: var(--color-ink-medium);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.empty-action:hover {
  transform: translateY(-1px);
  border-color: rgba(192,57,43,0.16);
  color: var(--color-vermilion);
}

.empty-action--primary {
  border-color: transparent;
  background: linear-gradient(135deg, var(--color-vermilion), #b73325);
  color: #fff;
}

.empty-action--primary:hover {
  color: #fff;
}

.draft-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: 14px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(44,62,80,0.06);
  font-size: 0.85rem;
  color: rgba(52,73,94,0.65);
}

.draft-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-cyan);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.ref-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ref-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border: 1px solid rgba(44,62,80,0.08);
  border-radius: 14px;
  background: rgba(255,255,255,0.6);
  cursor: pointer;
  font-size: 0.88rem;
  color: var(--color-ink-medium);
  transition: all 0.3s ease;
}

.ref-toggle:hover {
  border-color: rgba(192,57,43,0.15);
  color: var(--color-vermilion);
}

.ref-toggle__mark {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-family: var(--font-poem);
  font-size: 0.85rem;
  color: var(--color-vermilion);
  background: rgba(192,57,43,0.06);
}

.ref-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ref-search {
  display: flex;
  gap: 8px;
}

.ref-search__input {
  flex: 1;
  height: 38px;
  padding: 0 14px;
  border: 1px solid rgba(44,62,80,0.1);
  border-radius: 10px;
  font-size: 0.85rem;
  color: var(--color-ink-dark);
  background: rgba(255,255,255,0.7);
  outline: none;
  transition: border-color 0.3s ease;
}

.ref-search__input:focus {
  border-color: var(--color-vermilion);
}

.ref-search__btn {
  padding: 0 16px;
  height: 38px;
  border: 1px solid rgba(44,62,80,0.1);
  border-radius: 10px;
  background: rgba(44,62,80,0.04);
  cursor: pointer;
  font-size: 0.82rem;
  color: var(--color-ink-medium);
  transition: all 0.3s ease;
}

.ref-search__btn:hover:not(:disabled) {
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
}

.ref-loading {
  text-align: center;
  font-size: 0.82rem;
  color: rgba(52,73,94,0.5);
  padding: 12px;
}

.ref-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}

.ref-card {
  padding: 14px;
  border: 1px solid rgba(44,62,80,0.06);
  border-radius: 14px;
  background: rgba(255,255,255,0.7);
}

.ref-card--from {
  border-color: rgba(192,57,43,0.12);
  background: rgba(255,247,244,0.6);
}

.ref-card--result {
  cursor: pointer;
  transition: all 0.3s ease;
}

.ref-card--result:hover {
  border-color: rgba(192,57,43,0.15);
  background: rgba(255,255,255,0.9);
}

.ref-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.ref-card__badge {
  font-size: 0.75rem;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(192,57,43,0.08);
  color: var(--color-vermilion);
  letter-spacing: 1px;
}

.ref-card__close {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1.1rem;
  color: rgba(52,73,94,0.4);
  border-radius: 50%;
  transition: all 0.2s ease;
}

.ref-card__close:hover {
  background: rgba(44,62,80,0.06);
  color: var(--color-vermilion);
}

.ref-card__title {
  margin: 0 0 4px;
  font-family: var(--font-title);
  font-size: 0.92rem;
  color: var(--color-ink-dark);
  letter-spacing: 1px;
}

.ref-card__author {
  margin: 0 0 8px;
  font-size: 0.78rem;
  color: rgba(52,73,94,0.5);
  letter-spacing: 0.5px;
}

.ref-card__content {
  padding-top: 8px;
  border-top: 1px dashed rgba(44,62,80,0.08);
}

.ref-card__line {
  margin: 0;
  font-family: var(--font-poem);
  font-size: 0.88rem;
  line-height: 2;
  color: var(--color-ink-dark);
  letter-spacing: 0.08em;
}

.ref-card__more {
  margin: 0;
  font-size: 0.82rem;
  color: rgba(52,73,94,0.4);
  text-align: center;
}

.imitate-banner {
  margin-bottom: 24px;
  padding: 20px;
  border-radius: 18px;
  border: 1px solid rgba(22,160,133,0.15);
  background:
    linear-gradient(135deg, rgba(232,245,242,0.7), rgba(255,255,255,0.6));
  box-shadow: 0 8px 24px rgba(22,160,133,0.08);
}

.imitate-banner__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.imitate-banner__badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(22,160,133,0.12);
  color: var(--color-cyan, #16a085);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.12em;
}

.imitate-banner__exit {
  padding: 4px 12px;
  border: 1px solid rgba(44,62,80,0.1);
  border-radius: 999px;
  background: transparent;
  color: rgba(52,73,94,0.5);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.imitate-banner__exit:hover {
  border-color: rgba(192,57,43,0.2);
  color: var(--color-vermilion);
}

.imitate-banner__poem {
  margin-bottom: 12px;
  padding: 14px;
  border-radius: 12px;
  background: rgba(255,255,255,0.7);
  border: 1px dashed rgba(22,160,133,0.12);
}

.imitate-banner__title {
  margin: 0 0 4px;
  font-family: var(--font-title);
  font-size: 0.95rem;
  color: var(--color-ink-dark);
  letter-spacing: 0.08em;
}

.imitate-banner__author {
  margin: 0 0 8px;
  font-size: 0.78rem;
  color: rgba(52,73,94,0.55);
}

.imitate-banner__preview {
  border-top: 1px solid rgba(44,62,80,0.06);
  padding-top: 8px;
}

.imitate-banner__line {
  margin: 0;
  font-family: var(--font-poem);
  font-size: 0.85rem;
  line-height: 2;
  color: var(--color-ink-dark);
  letter-spacing: 0.06em;
}

.imitate-banner__more {
  margin: 0;
  font-size: 0.78rem;
  color: rgba(52,73,94,0.4);
}

.imitate-banner__struct {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 0.82rem;
}

.imitate-banner__struct-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgba(22,160,133,0.08);
  color: var(--color-cyan, #16a085);
  font-size: 0.72rem;
  font-weight: 600;
}

.imitate-banner__struct-value {
  color: rgba(52,73,94,0.7);
}

.imitate-banner__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.imitate-banner__action {
  min-height: 34px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(44,62,80,0.1);
  background: rgba(255,255,255,0.72);
  color: var(--color-ink-dark);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.imitate-banner__action:hover {
  transform: translateY(-1px);
  border-color: rgba(22,160,133,0.2);
  color: var(--color-cyan, #16a085);
}

.imitate-banner__action--primary {
  border-color: transparent;
  background: linear-gradient(135deg, var(--color-cyan, #16a085), #1abc9c);
  color: #fff;
  box-shadow: 0 6px 16px rgba(22,160,133,0.2);
}

.imitate-banner__action--primary:hover {
  color: #fff;
  box-shadow: 0 8px 20px rgba(22,160,133,0.28);
}

.ai-sidebar {
  flex: 0 0 360px;
  position: sticky;
  top: 92px;
  max-height: calc(100vh - 124px);
  display: flex;
  flex-direction: column;
}

.ai-assistant-card {
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(178,141,87,0.12);
  box-shadow: 0 20px 50px rgba(44,62,80,0.08);
  overflow: hidden;
  height: 100%;
  position: relative;
}

.ai-assistant-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-gold, #b28d57), rgba(178,141,87,0.3), transparent);
  border-radius: 24px 24px 0 0;
}

.ai-assistant-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(178,141,87,0.08);
  flex-shrink: 0;
}

.ai-assistant-card__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-gold, #b28d57);
  animation: aiPulse 2s ease-in-out infinite;
}

.ai-assistant-card__title {
  font-family: var(--font-title);
  font-size: 0.92rem;
  color: var(--color-ink-dark);
  letter-spacing: 0.12em;
  flex: 1;
}

.ai-assistant-card__clear {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1.1rem;
  color: rgba(52,73,94,0.4);
  border-radius: 50%;
  transition: all 0.2s ease;
}

.ai-assistant-card__clear:hover {
  background: rgba(44,62,80,0.06);
  color: var(--color-vermilion);
}

.ai-assistant-card .ai-chat-scroll {
  flex: 1;
  max-height: none;
  overflow-y: auto;
}

.ai-sidebar-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  justify-content: center;
}

.ai-sidebar-topic {
  min-height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px dashed rgba(178,141,87,0.2);
  background: rgba(178,141,87,0.04);
  color: rgba(52,73,94,0.65);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.25s ease;
}

.ai-sidebar-topic:hover {
  border-color: var(--color-gold, #b28d57);
  color: var(--color-gold, #b28d57);
  background: rgba(178,141,87,0.08);
  transform: translateY(-1px);
}

@media (min-width: 1281px) and (max-width: 1559px) {
  .ai-sidebar {
    flex: 0 0 320px;
  }

  .preview-panel {
    flex: 0 0 280px;
  }
}

@media (max-width: 1280px) {
  .create-body {
    flex-wrap: wrap;
    padding: 24px;
  }

  .editor-panel {
    flex: 1 1 100%;
  }

  .preview-panel {
    flex: 1 1 calc(50% - 12px);
  }

  .ai-sidebar {
    flex: 1 1 calc(50% - 12px);
    position: static;
    max-height: none;
  }

  .ai-assistant-card {
    max-height: 600px;
  }

  .preview-card {
    position: static;
    max-height: none;
  }
}

@media (max-width: 960px) {
  .create-body {
    flex-direction: column;
    padding: 20px;
  }

  .preview-panel,
  .ai-sidebar {
    flex: none;
    width: 100%;
  }

  .preview-card {
    min-height: 360px;
  }

  .create-nav {
    padding: 0 16px;
  }

  .nav-title {
    display: none;
  }
}

@media (max-width: 640px) {
  .starter-guide__header,
  .starter-guide__actions,
  .empty-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .editor-card {
    padding: 22px;
  }

  .scroll-body {
    padding: 32px 24px;
  }

  .ai-assistant-card {
    max-height: 500px;
  }
}
</style>

<style>
.ai-chat-scroll::-webkit-scrollbar {
  width: 5px;
}
.ai-chat-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.ai-chat-scroll::-webkit-scrollbar-thumb {
  background: rgba(178,141,87,0.2);
  border-radius: 3px;
}
.ai-chat-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(178,141,87,0.35);
}
</style>
