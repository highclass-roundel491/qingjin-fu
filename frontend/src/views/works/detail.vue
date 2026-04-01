<template>
  <div class="detail-page">
    <div class="ink-bg">
      <div class="ink-wash ink-wash--1"></div>
      <div class="ink-wash ink-wash--2"></div>
    </div>

    <nav class="page-nav">
      <router-link to="/works" class="nav-back">← 作品墙</router-link>
      <span class="nav-title">作品详情</span>
      <div class="nav-actions" v-if="isOwner">
        <button v-if="work?.status === 'draft'" class="btn-edit" @click="goEdit">编辑</button>
        <button v-if="work?.status === 'published'" class="btn-unpublish" @click="handleUnpublish">撤回</button>
        <button class="btn-delete" @click="handleDelete">删除</button>
      </div>
      <div v-else class="nav-actions"></div>
    </nav>

    <main class="page-body" v-if="work">
      <div class="scroll-container">
        <div class="scroll-card">
          <div class="scroll-corner scroll-corner--tl"></div>
          <div class="scroll-corner scroll-corner--tr"></div>
          <div class="scroll-corner scroll-corner--bl"></div>
          <div class="scroll-corner scroll-corner--br"></div>

          <div class="scroll-meta">
            <span class="scroll-genre-tag">{{ work.genre }}</span>
            <span v-if="work.status === 'draft'" class="scroll-draft-tag">草稿</span>
          </div>

          <h1 class="scroll-title">{{ work.title }}</h1>
          <div class="scroll-divider"></div>

          <div class="scroll-content">
            <p
              v-for="(line, i) in contentLines"
              :key="i"
              class="scroll-line"
              :style="{ animationDelay: `${i * 0.15}s` }"
            >{{ line }}</p>
          </div>

          <div class="scroll-author-block">
            <div class="scroll-author-info">
              <UserAvatar :username="work.username" :avatar="work.avatar_url" size="small" />
              <span class="scroll-author-name">{{ work.username }}</span>
            </div>
            <span class="scroll-date">{{ formatDate(work.published_at || work.created_at) }}</span>
          </div>
        </div>

        <div class="action-bar">
          <button
            class="action-btn action-btn--like"
            :class="{ 'action-btn--liked': work.is_liked }"
            @click="toggleLike"
          >
            <span class="action-icon">♥</span>
            <span>{{ work.like_count }}</span>
          </button>
          <div class="action-stat">
            <span class="action-icon">👁</span>
            <span>{{ work.view_count }}</span>
          </div>
          <div class="action-stat">
            <span class="action-icon">💬</span>
            <span>{{ work.comment_count || 0 }}</span>
          </div>
        </div>

        <div v-if="work.ai_total_score" class="ai-score-card">
          <div class="ai-header">
            <span class="ai-badge">AI 评分</span>
            <span class="ai-total">{{ work.ai_total_score }}分</span>
          </div>
          <div class="ai-scores">
            <div class="ai-score-item">
              <span class="ai-score-label">格律</span>
              <div class="ai-score-bar">
                <div class="ai-score-fill ai-score-fill--grammar" :style="{ width: `${work.ai_grammar_score || 0}%` }"></div>
              </div>
              <span class="ai-score-value">{{ work.ai_grammar_score || 0 }}</span>
            </div>
            <div class="ai-score-item">
              <span class="ai-score-label">意境</span>
              <div class="ai-score-bar">
                <div class="ai-score-fill ai-score-fill--artistic" :style="{ width: `${work.ai_artistic_score || 0}%` }"></div>
              </div>
              <span class="ai-score-value">{{ work.ai_artistic_score || 0 }}</span>
            </div>
          </div>
          <p v-if="work.ai_feedback" class="ai-feedback">{{ work.ai_feedback }}</p>
          <button
            v-if="isOwner && userStore.isLogin"
            class="ai-rescore-btn"
            :disabled="aiScoring"
            @click="requestAIScore"
          >{{ aiScoring ? '评分中...' : '重新评分' }}</button>
          <AiPhaseStatus
            v-if="aiScoring"
            title="翰林评分中"
            :stages="aiScoreStages"
            :current="aiScoreStep"
            hint="正在分析格律、意境并生成评语"
          />
        </div>
        <div v-else-if="isOwner && userStore.isLogin && work.status === 'published'" class="ai-score-card ai-score-card--empty">
          <p class="ai-empty-text">尚未获得 AI 评分</p>
          <button class="ai-request-btn" :disabled="aiScoring" @click="requestAIScore">
            {{ aiScoring ? '评分中...' : '请求 AI 评分' }}
          </button>
          <AiPhaseStatus
            v-if="aiScoring"
            title="翰林评分中"
            :stages="aiScoreStages"
            :current="aiScoreStep"
            hint="完成后将展示总分与分项评分"
          />
        </div>

        <section class="comment-section" v-if="work.status === 'published'">
          <div class="comment-header">
            <span class="comment-header-title">品鉴留墨</span>
            <span class="comment-header-count" v-if="commentTotal > 0">{{ commentTotal }}</span>
          </div>

          <div class="comment-composer" v-if="userStore.isLogin">
            <UserAvatar :username="userStore.userInfo?.username || ''" :avatar="userStore.userInfo?.avatar_url" size="small" />
            <div class="composer-body">
              <div v-if="replyTarget" class="composer-reply-hint">
                <span>回复 @{{ replyTarget.username }}</span>
                <button class="composer-reply-cancel" @click="cancelReply">取消</button>
              </div>
              <textarea
                ref="composerInput"
                v-model="commentText"
                class="composer-textarea"
                :placeholder="replyTarget ? `回复 ${replyTarget.username}...` : '留下你的品鉴...'"
                rows="2"
                maxlength="500"
                @keydown.ctrl.enter="submitComment"
                @keydown.meta.enter="submitComment"
              ></textarea>
              <div class="composer-footer">
                <span class="composer-char-count">{{ commentText.length }}/500</span>
                <button class="composer-submit" :disabled="!commentText.trim() || submitting" @click="submitComment">
                  {{ submitting ? '...' : '落笔' }}
                </button>
              </div>
            </div>
          </div>
          <div v-else class="comment-login-hint">
            <router-link to="/login">登录</router-link>后方可留墨
          </div>

          <div class="comment-list" v-if="comments.length > 0">
            <div
              v-for="(comment, ci) in comments"
              :key="comment.id"
              class="comment-item"
              :style="{ animationDelay: `${ci * 0.05}s` }"
            >
              <div class="comment-main">
                <div class="comment-avatar" @click="goToUser(comment.user_id)">
                  <UserAvatar :username="comment.username" :avatar="comment.avatar_url" size="small" :clickable="true" />
                </div>
                <div class="comment-body">
                  <div class="comment-meta">
                    <span class="comment-author" @click="goToUser(comment.user_id)">{{ comment.nickname || comment.username }}</span>
                    <span class="comment-time">{{ formatRelativeTime(comment.created_at) }}</span>
                  </div>
                  <p class="comment-content">{{ comment.content }}</p>
                  <div class="comment-actions">
                    <button class="comment-action" :class="{ 'comment-action--liked': comment.is_liked }" @click="toggleCommentLike(comment)">
                      <span>♥</span>
                      <span v-if="comment.like_count > 0">{{ comment.like_count }}</span>
                    </button>
                    <button class="comment-action" @click="setReply(comment)">回复</button>
                    <button
                      v-if="canDeleteComment(comment)"
                      class="comment-action comment-action--delete"
                      @click="deleteCommentById(comment.id)"
                    >删除</button>
                  </div>
                </div>
              </div>

              <div v-if="comment.replies && comment.replies.length > 0" class="comment-replies">
                <div
                  v-for="reply in comment.replies"
                  :key="reply.id"
                  class="comment-reply"
                >
                  <div class="comment-avatar comment-avatar--sm" @click="goToUser(reply.user_id)">
                    <UserAvatar :username="reply.username" :avatar="reply.avatar_url" size="small" :clickable="true" />
                  </div>
                  <div class="comment-body">
                    <div class="comment-meta">
                      <span class="comment-author" @click="goToUser(reply.user_id)">{{ reply.nickname || reply.username }}</span>
                      <span v-if="reply.reply_to_username" class="comment-reply-to">
                        回复 <span class="comment-reply-to-name">@{{ reply.reply_to_username }}</span>
                      </span>
                      <span class="comment-time">{{ formatRelativeTime(reply.created_at) }}</span>
                    </div>
                    <p class="comment-content">{{ reply.content }}</p>
                    <div class="comment-actions">
                      <button class="comment-action" :class="{ 'comment-action--liked': reply.is_liked }" @click="toggleCommentLike(reply)">
                        <span>♥</span>
                        <span v-if="reply.like_count > 0">{{ reply.like_count }}</span>
                      </button>
                      <button class="comment-action" @click="setReply(reply, comment)">回复</button>
                      <button
                        v-if="canDeleteComment(reply)"
                        class="comment-action comment-action--delete"
                        @click="deleteCommentById(reply.id)"
                      >删除</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="!commentLoading" class="comment-empty">
            <span class="comment-empty-text">尚无品鉴，留下第一笔墨迹吧</span>
          </div>

          <div v-if="commentLoading" class="comment-loading">
            <span>加载中...</span>
          </div>

          <div v-if="comments.length > 0 && comments.length < commentTotal" class="comment-load-more">
            <button class="comment-more-btn" @click="loadMoreComments" :disabled="commentLoading">
              {{ commentLoading ? '加载中...' : '查看更多品鉴' }}
            </button>
          </div>
        </section>

        <section class="next-steps" v-if="work.status === 'published'">
          <div class="next-steps-header">
            <span class="next-steps-line"></span>
            <span class="next-steps-label">继续探索</span>
            <span class="next-steps-line"></span>
          </div>
          <div class="next-steps-grid">
            <router-link to="/works" class="next-step-card">
              <span class="next-step-icon">墙</span>
              <span class="next-step-text">浏览更多作品</span>
            </router-link>
            <router-link to="/works/create" class="next-step-card next-step-card--accent">
              <span class="next-step-icon">笔</span>
              <span class="next-step-text">我也来创作</span>
            </router-link>
            <router-link to="/works/rankings" class="next-step-card">
              <span class="next-step-icon">榜</span>
              <span class="next-step-text">创作排行榜</span>
            </router-link>
            <router-link :to="`/user/${work.user_id}`" class="next-step-card" v-if="!isOwner">
              <span class="next-step-icon">友</span>
              <span class="next-step-text">查看作者主页</span>
            </router-link>
            <router-link to="/poems" class="next-step-card" v-if="isOwner">
              <span class="next-step-icon">学</span>
              <span class="next-step-text">诗词学堂</span>
            </router-link>
          </div>
        </section>
      </div>
    </main>

    <div v-else-if="loading" class="loading-state">
      <div class="loading-dot"></div>
      <span>加载中…</span>
    </div>

    <AppToast v-model="toast.show" :message="toast.message" :type="toast.type" />
    <AppConfirm
      v-model="confirmVisible"
      title="删除作品"
      message="确定要删除这篇作品吗？此操作不可恢复。"
      confirm-text="删除"
      variant="danger"
      @confirm="doDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { worksApi, type WorkDetail } from '@/api/works'
import { commentsApi, type CommentItem } from '@/api/comments'
import { useUserStore } from '@/store/modules/user'
import UserAvatar from '@/components/UserAvatar.vue'
import AppToast from '@/components/AppToast.vue'
import AppConfirm from '@/components/AppConfirm.vue'
import AiPhaseStatus from '@/components/AiPhaseStatus.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const work = ref<WorkDetail | null>(null)
const loading = ref(true)
const aiScoring = ref(false)
const aiScoreStep = ref(0)
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' | 'warning' | 'info' })
const confirmVisible = ref(false)
const aiScoreStages = ['解析作品文本', '评估格律意境', '生成评分反馈']
const aiScoreTimer = ref<number | null>(null)

function clearAIScoreTimer() {
  if (aiScoreTimer.value !== null) {
    clearInterval(aiScoreTimer.value)
    aiScoreTimer.value = null
  }
}

const isOwner = computed(() =>
  work.value && userStore.userInfo && work.value.user_id === userStore.userInfo.id
)

const contentLines = computed(() =>
  (work.value?.content || '').split('\n').map(l => l.trim()).filter(l => l.length > 0)
)

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

function showToast(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'success') {
  toast.value = { show: true, message, type }
}

async function fetchWork() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    work.value = await worksApi.getWorkDetail(id)
  } catch {
    showToast('作品不存在或无权查看', 'error')
  }
  loading.value = false
}

async function toggleLike() {
  if (!work.value) return
  try {
    if (work.value.is_liked) {
      await worksApi.unlikeWork(work.value.id)
      work.value.is_liked = false
      work.value.like_count = Math.max(0, work.value.like_count - 1)
    } else {
      await worksApi.likeWork(work.value.id)
      work.value.is_liked = true
      work.value.like_count++
    }
  } catch {}
}

function goEdit() {
  if (work.value) {
    router.push(`/works/create?id=${work.value.id}`)
  }
}

async function requestAIScore() {
  if (!work.value || aiScoring.value) return
  aiScoring.value = true
  aiScoreStep.value = 0
  clearAIScoreTimer()
  aiScoreTimer.value = window.setInterval(() => {
    if (aiScoreStep.value < aiScoreStages.length - 1) {
      aiScoreStep.value += 1
      return
    }
    clearAIScoreTimer()
  }, 2200)
  try {
    const res = await worksApi.scoreWorkWithAI(work.value.id)
    work.value.ai_grammar_score = res.grammar_score
    work.value.ai_artistic_score = res.artistic_score
    work.value.ai_total_score = res.total_score
    work.value.ai_feedback = res.feedback
    showToast('AI 评分完成')
  } catch (e: any) {
    showToast(e?.response?.data?.detail || 'AI 评分失败', 'error')
  } finally {
    clearAIScoreTimer()
    aiScoreStep.value = 0
    aiScoring.value = false
  }
}

async function handleUnpublish() {
  if (!work.value) return
  try {
    await worksApi.unpublishWork(work.value.id)
    work.value.status = 'draft'
    work.value.published_at = null
    showToast('已撤回至草稿')
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '操作失败', 'error')
  }
}

function handleDelete() {
  if (!work.value) return
  confirmVisible.value = true
}

async function doDelete() {
  if (!work.value) return
  try {
    await worksApi.deleteWork(work.value.id)
    showToast('作品已删除')
    setTimeout(() => router.push('/works'), 1000)
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '删除失败', 'error')
  }
}

const comments = ref<CommentItem[]>([])
const commentTotal = ref(0)
const commentPage = ref(1)
const commentLoading = ref(false)
const commentText = ref('')
const submitting = ref(false)
const replyTarget = ref<{ id: number; username: string; parentId?: number } | null>(null)
const composerInput = ref<HTMLTextAreaElement | null>(null)

async function fetchComments() {
  if (!work.value) return
  commentLoading.value = true
  try {
    const res = await commentsApi.getComments(work.value.id, { page: commentPage.value, page_size: 15 })
    if (commentPage.value === 1) {
      comments.value = res.items
    } else {
      comments.value.push(...res.items)
    }
    commentTotal.value = res.total
  } catch {}
  commentLoading.value = false
}

function loadMoreComments() {
  commentPage.value++
  fetchComments()
}

async function submitComment() {
  if (!work.value || !commentText.value.trim() || submitting.value) return
  submitting.value = true
  try {
    const parentId = replyTarget.value?.parentId ?? replyTarget.value?.id ?? null
    const newComment = await commentsApi.createComment(work.value.id, {
      content: commentText.value.trim(),
      parent_id: parentId
    })
    if (parentId) {
      const parent = comments.value.find(c => c.id === parentId)
      if (parent) {
        parent.replies = [...(parent.replies || []), newComment]
      }
    } else {
      comments.value.unshift(newComment)
    }
    commentTotal.value++
    if (work.value) work.value.comment_count = (work.value.comment_count || 0) + 1
    commentText.value = ''
    replyTarget.value = null
  } catch {}
  submitting.value = false
}

function setReply(comment: CommentItem, parentComment?: CommentItem) {
  replyTarget.value = {
    id: comment.id,
    username: comment.nickname || comment.username,
    parentId: parentComment?.id
  }
  nextTick(() => composerInput.value?.focus())
}

function cancelReply() {
  replyTarget.value = null
}

async function toggleCommentLike(comment: CommentItem) {
  if (!work.value) return
  try {
    if (comment.is_liked) {
      await commentsApi.unlikeComment(work.value.id, comment.id)
      comment.is_liked = false
      comment.like_count = Math.max(0, comment.like_count - 1)
    } else {
      await commentsApi.likeComment(work.value.id, comment.id)
      comment.is_liked = true
      comment.like_count++
    }
  } catch {}
}

function canDeleteComment(comment: CommentItem) {
  if (!userStore.userInfo) return false
  if (comment.user_id === userStore.userInfo.id) return true
  if (work.value && work.value.user_id === userStore.userInfo.id) return true
  return false
}

async function deleteCommentById(commentId: number) {
  if (!work.value) return
  try {
    await commentsApi.deleteComment(work.value.id, commentId)
    const topIdx = comments.value.findIndex(c => c.id === commentId)
    if (topIdx !== -1) {
      const removed = comments.value.splice(topIdx, 1)[0]!
      const removedCount = 1 + (removed.replies?.length || 0)
      commentTotal.value = Math.max(0, commentTotal.value - removedCount)
      if (work.value) work.value.comment_count = Math.max(0, (work.value.comment_count || 0) - removedCount)
    } else {
      for (const c of comments.value) {
        if (c.replies) {
          const ri = c.replies.findIndex(r => r.id === commentId)
          if (ri !== -1) {
            c.replies.splice(ri, 1)
            commentTotal.value = Math.max(0, commentTotal.value - 1)
            if (work.value) work.value.comment_count = Math.max(0, (work.value.comment_count || 0) - 1)
            break
          }
        }
      }
    }
    showToast('评论已删除')
  } catch {
    showToast('删除失败', 'error')
  }
}

function goToUser(userId: number) {
  router.push(`/user/${userId}`)
}

function formatRelativeTime(dateStr: string) {
  const now = Date.now()
  const d = new Date(dateStr).getTime()
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

onMounted(async () => {
  await fetchWork()
  if (work.value?.status === 'published') {
    fetchComments()
  }
})
</script>

<style scoped>
.detail-page {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(170deg, #f6f1e8 0%, #fdfefe 40%, #f0ebe2 100%);
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
  opacity: 0.15;
}

.ink-wash--1 {
  width: 500px;
  height: 500px;
  top: -180px;
  right: -100px;
  background: radial-gradient(circle, rgba(192,57,43,0.28), transparent 70%);
}

.ink-wash--2 {
  width: 400px;
  height: 400px;
  bottom: -120px;
  left: -60px;
  background: radial-gradient(circle, rgba(22,160,133,0.22), transparent 70%);
}

.page-nav {
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
}

.nav-back:hover { color: var(--color-vermilion); }

.nav-title {
  font-family: var(--font-poem);
  font-size: 1.15rem;
  letter-spacing: 0.2em;
  color: var(--color-ink-dark);
}

.nav-actions {
  display: flex;
  gap: 8px;
}

.btn-edit, .btn-unpublish, .btn-delete {
  height: 34px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 0.85rem;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.btn-edit {
  background: rgba(22,160,133,0.1);
  color: var(--color-cyan);
}

.btn-edit:hover { background: rgba(22,160,133,0.18); }

.btn-unpublish {
  background: rgba(243,156,18,0.1);
  color: var(--color-warning);
}

.btn-unpublish:hover { background: rgba(243,156,18,0.18); }

.btn-delete {
  background: rgba(231,76,60,0.08);
  color: var(--color-error);
}

.btn-delete:hover { background: rgba(231,76,60,0.15); }

.page-body {
  position: relative;
  z-index: 1;
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 24px;
}

.scroll-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.scroll-card {
  position: relative;
  padding: 56px 48px;
  border-radius: 24px;
  background:
    radial-gradient(ellipse at top left, rgba(246,241,232,0.96), transparent 55%),
    linear-gradient(180deg, rgba(253,249,240,0.98), rgba(246,241,232,0.98));
  border: 1px solid rgba(44,62,80,0.08);
  box-shadow: 0 24px 56px rgba(44,62,80,0.1);
  text-align: center;
  overflow: hidden;
}

.scroll-corner {
  position: absolute;
  width: 28px;
  height: 28px;
  border-color: rgba(192,57,43,0.12);
  border-style: solid;
}

.scroll-corner--tl { top: 16px; left: 16px; border-width: 1px 0 0 1px; }
.scroll-corner--tr { top: 16px; right: 16px; border-width: 1px 1px 0 0; }
.scroll-corner--bl { bottom: 16px; left: 16px; border-width: 0 0 1px 1px; }
.scroll-corner--br { bottom: 16px; right: 16px; border-width: 0 1px 1px 0; }

.scroll-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}

.scroll-genre-tag {
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 0.82rem;
  background: rgba(44,62,80,0.06);
  color: rgba(52,73,94,0.65);
}

.scroll-draft-tag {
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 0.82rem;
  background: rgba(243,156,18,0.12);
  color: var(--color-warning);
}

.scroll-title {
  font-family: var(--font-title);
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  color: var(--color-ink-dark);
  margin-bottom: 16px;
  letter-spacing: 0.08em;
}

.scroll-divider {
  width: 56px;
  height: 2px;
  margin: 0 auto 36px;
  background: linear-gradient(90deg, transparent, var(--color-vermilion), transparent);
  opacity: 0.5;
}

.scroll-content {
  margin-bottom: 40px;
}

.scroll-line {
  font-family: var(--font-poem);
  font-size: clamp(1.2rem, 2.5vw, 1.45rem);
  line-height: 2.6;
  color: var(--color-ink-dark);
  letter-spacing: 0.18em;
  animation: lineReveal 0.6s ease both;
}

@keyframes lineReveal {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.scroll-author-block {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 24px;
  border-top: 1px solid rgba(44,62,80,0.06);
}

.scroll-author-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.scroll-author-name {
  font-size: 0.92rem;
  color: var(--color-ink-medium);
}

.scroll-date {
  font-size: 0.85rem;
  color: rgba(52,73,94,0.5);
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(44,62,80,0.06);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 999px;
  font-size: 0.92rem;
  cursor: pointer;
  border: 1px solid rgba(44,62,80,0.1);
  background: rgba(255,255,255,0.8);
  color: var(--color-ink-medium);
  transition: all var(--transition-fast);
}

.action-btn--like:hover,
.action-btn--liked {
  border-color: rgba(192,57,43,0.2);
  color: var(--color-vermilion);
  background: rgba(192,57,43,0.06);
}

.action-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.92rem;
  color: rgba(52,73,94,0.55);
}

.action-icon {
  font-size: 1rem;
}

.ai-score-card {
  padding: 24px;
  border-radius: 20px;
  background: rgba(255,255,255,0.75);
  border: 1px solid rgba(44,62,80,0.07);
  box-shadow: 0 8px 24px rgba(44,62,80,0.05);
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.ai-badge {
  font-size: 0.88rem;
  font-weight: 600;
  padding: 4px 14px;
  border-radius: 999px;
  background: rgba(22,160,133,0.1);
  color: var(--color-cyan);
}

.ai-total {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-ink-dark);
  font-family: var(--font-title);
}

.ai-scores {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}

.ai-score-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-score-label {
  width: 32px;
  font-size: 0.85rem;
  color: rgba(52,73,94,0.7);
  flex-shrink: 0;
}

.ai-score-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: rgba(44,62,80,0.06);
  overflow: hidden;
}

.ai-score-fill {
  height: 100%;
  border-radius: inherit;
  transition: width 1s ease;
}

.ai-score-fill--grammar {
  background: linear-gradient(90deg, var(--color-cyan), #2ecc71);
}

.ai-score-fill--artistic {
  background: linear-gradient(90deg, var(--color-vermilion), #e67e22);
}

.ai-score-value {
  width: 28px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-ink-dark);
  text-align: right;
  flex-shrink: 0;
}

.ai-feedback {
  font-size: 0.9rem;
  line-height: 1.8;
  color: rgba(44,62,80,0.75);
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(44,62,80,0.03);
}

.ai-rescore-btn {
  display: block;
  margin: 14px auto 0;
  padding: 6px 20px;
  border-radius: 999px;
  font-size: 0.82rem;
  color: var(--color-ink-medium);
  background: rgba(44,62,80,0.05);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ai-rescore-btn:hover:not(:disabled) {
  background: rgba(44,62,80,0.1);
  color: var(--color-ink-dark);
}

.ai-rescore-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-score-card--empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 28px 24px;
}

.ai-empty-text {
  font-size: 0.9rem;
  color: rgba(52,73,94,0.5);
}

.ai-request-btn {
  padding: 8px 28px;
  border-radius: 999px;
  font-size: 0.88rem;
  font-family: var(--font-title);
  letter-spacing: 0.1em;
  color: #fff;
  background: linear-gradient(135deg, var(--color-cyan), #2ecc71);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: 0 4px 12px rgba(22,160,133,0.2);
}

.ai-request-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(22,160,133,0.3);
}

.ai-request-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 120px 0;
  color: rgba(52,73,94,0.5);
  font-size: 0.92rem;
}

.loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-vermilion);
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.8); }
}

@media (max-width: 640px) {
  .scroll-card {
    padding: 36px 24px;
  }

  .page-body {
    padding: 24px 16px;
  }

  .comment-composer {
    gap: 10px;
    padding: 14px;
  }

  .comment-main, .comment-reply {
    gap: 10px;
  }

  .comment-replies {
    margin-left: 24px;
  }
}

.comment-section {
  padding: 28px 0 8px;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.comment-header-title {
  font-family: var(--font-title);
  font-size: 1.1rem;
  letter-spacing: 0.15em;
  color: var(--color-ink-dark);
}

.comment-header-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 11px;
  background: rgba(44,62,80,0.07);
  font-size: 0.78rem;
  color: var(--color-ink-medium);
  font-family: var(--font-body);
}

.comment-composer {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 20px;
  border-radius: 16px;
  background: rgba(255,255,255,0.65);
  border: 1px solid rgba(44,62,80,0.06);
  margin-bottom: 20px;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.comment-composer:focus-within {
  border-color: rgba(69,104,93,0.2);
  box-shadow: 0 4px 16px rgba(44,62,80,0.05);
}

.composer-body {
  flex: 1;
  min-width: 0;
}

.composer-reply-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(69,104,93,0.06);
  font-size: 0.82rem;
  color: var(--color-cyan);
}

.composer-reply-cancel {
  font-size: 0.78rem;
  color: var(--color-ink-medium);
  opacity: 0.5;
  background: none;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.composer-reply-cancel:hover {
  opacity: 0.8;
}

.composer-textarea {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-family: var(--font-poem);
  font-size: 0.92rem;
  line-height: 1.8;
  color: var(--color-ink-dark);
  resize: vertical;
  min-height: 48px;
  max-height: 160px;
}

.composer-textarea::placeholder {
  color: var(--color-ink-medium);
  opacity: 0.3;
  font-family: var(--font-poem);
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.composer-char-count {
  font-size: 0.75rem;
  color: var(--color-ink-medium);
  opacity: 0.3;
}

.composer-submit {
  padding: 6px 20px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-family: var(--font-title);
  letter-spacing: 0.1em;
  background: var(--color-ink-dark);
  color: var(--color-paper-white);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.composer-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(18,17,16,0.15);
}

.composer-submit:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.comment-login-hint {
  text-align: center;
  padding: 16px;
  font-size: 0.88rem;
  color: var(--color-ink-medium);
  opacity: 0.5;
  margin-bottom: 20px;
}

.comment-login-hint a {
  color: var(--color-vermilion);
  font-weight: 500;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.comment-item {
  animation: commentFadeIn 0.35s ease backwards;
}

@keyframes commentFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.comment-main {
  display: flex;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(44,62,80,0.04);
}

.comment-avatar {
  flex-shrink: 0;
  cursor: pointer;
}

.comment-avatar--sm {
  transform: scale(0.85);
  transform-origin: top center;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.comment-author {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-ink-dark);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.comment-author:hover {
  color: var(--color-vermilion);
}

.comment-reply-to {
  font-size: 0.78rem;
  color: var(--color-ink-medium);
  opacity: 0.45;
}

.comment-reply-to-name {
  color: var(--color-cyan);
  opacity: 1;
}

.comment-time {
  font-size: 0.75rem;
  color: var(--color-ink-medium);
  opacity: 0.35;
}

.comment-content {
  font-size: 0.9rem;
  line-height: 1.7;
  color: rgba(44,62,80,0.82);
  word-break: break-word;
  margin-bottom: 6px;
}

.comment-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.comment-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--color-ink-medium);
  opacity: 0.35;
  background: none;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.comment-action:hover {
  opacity: 0.7;
  background: rgba(44,62,80,0.03);
}

.comment-action--liked {
  color: var(--color-vermilion);
  opacity: 0.8;
}

.comment-action--liked:hover {
  opacity: 1;
}

.comment-action--delete:hover {
  color: var(--color-error);
  opacity: 0.7;
}

.comment-replies {
  margin-left: 50px;
  border-left: 2px solid rgba(44,62,80,0.04);
  padding-left: 16px;
}

.comment-reply {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(44,62,80,0.03);
}

.comment-reply:last-child {
  border-bottom: none;
}

.comment-empty {
  text-align: center;
  padding: 36px 0;
}

.comment-empty-text {
  font-family: var(--font-poem);
  font-size: 0.9rem;
  color: var(--color-ink-medium);
  opacity: 0.3;
  letter-spacing: 0.1em;
}

.comment-loading {
  text-align: center;
  padding: 20px 0;
  font-size: 0.85rem;
  color: var(--color-ink-medium);
  opacity: 0.35;
}

.comment-load-more {
  text-align: center;
  padding: 16px 0;
}

.comment-more-btn {
  padding: 8px 28px;
  border-radius: 999px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(44,62,80,0.08);
  font-size: 0.85rem;
  font-family: var(--font-title);
  letter-spacing: 0.08em;
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.comment-more-btn:hover:not(:disabled) {
  border-color: var(--color-ink-medium);
  transform: translateY(-1px);
}

.comment-more-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.next-steps {
  padding: 32px 0 8px;
}

.next-steps-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.next-steps-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(44,62,80,0.08), transparent);
}

.next-steps-label {
  font-family: var(--font-title);
  font-size: 0.88rem;
  letter-spacing: 0.2em;
  color: rgba(52,73,94,0.4);
  flex-shrink: 0;
}

.next-steps-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.next-step-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(255,255,255,0.6);
  border: 1px solid rgba(44,62,80,0.06);
  text-decoration: none;
  color: var(--color-ink-dark);
  transition: all var(--transition-fast);
}

.next-step-card:hover {
  border-color: rgba(44,62,80,0.12);
  box-shadow: 0 4px 16px rgba(44,62,80,0.06);
  transform: translateY(-2px);
}

.next-step-card--accent {
  background: rgba(192,57,43,0.04);
  border-color: rgba(192,57,43,0.1);
}

.next-step-card--accent:hover {
  border-color: rgba(192,57,43,0.2);
  box-shadow: 0 4px 16px rgba(192,57,43,0.08);
}

.next-step-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(44,62,80,0.04);
  font-family: var(--font-title);
  font-size: 0.88rem;
  color: var(--color-ink-medium);
  flex-shrink: 0;
}

.next-step-card--accent .next-step-icon {
  background: rgba(192,57,43,0.08);
  color: var(--color-vermilion);
}

.next-step-text {
  font-size: 0.9rem;
  font-weight: 500;
}

@media (max-width: 480px) {
  .next-steps-grid {
    grid-template-columns: 1fr;
  }
}
</style>
