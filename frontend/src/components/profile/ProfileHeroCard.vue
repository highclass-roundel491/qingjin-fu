<template>
  <aside class="profile-hero">
    <div class="profile-hero__mist profile-hero__mist--top"></div>
    <div class="profile-hero__mist profile-hero__mist--bottom"></div>

    <div class="profile-hero__main">
      <div class="profile-hero__identity-block">
        <div class="profile-hero__avatar-shell">
          <div class="profile-hero__avatar-ring"></div>
          <UserAvatar
            :username="safeUsername"
            :avatar="user?.avatar_url"
            size="large"
          />
        </div>

        <div class="profile-hero__identity">
          <div class="profile-hero__identity-head">
            <p class="profile-hero__eyebrow">兰台藏录</p>
            <div class="profile-hero__seal">青衿卷</div>
          </div>
          <h1 class="profile-hero__name">{{ displayName }}</h1>
          <p class="profile-hero__username">@{{ safeUsername }}</p>
          <p class="profile-hero__bio">{{ displayBio }}</p>
        </div>
      </div>

      <div class="profile-hero__growth">
        <div class="profile-hero__rank-band" @click="$emit('showRanks')" style="cursor: pointer;">
          <img :src="rankInfo.icon" class="profile-hero__rank-icon" alt="" />
          <span class="profile-hero__rank-level">Lv.{{ currentLevel }}</span>
          <span class="profile-hero__rank-title">{{ levelTitle }}</span>
        </div>

        <div class="profile-hero__progress-block">
          <div class="profile-hero__progress-meta">
            <span>文采进度</span>
            <span>{{ currentExp }}/{{ nextLevelExp }}</span>
          </div>
          <div class="profile-hero__progress-track">
            <div class="profile-hero__progress-fill" :style="{ width: `${progressPercentage}%` }"></div>
          </div>
          <div class="profile-hero__progress-text">{{ progressText }}</div>
        </div>
      </div>
    </div>

    <div class="profile-hero__footer">
      <div class="profile-hero__chips">
        <div class="profile-hero__chip">
          <span class="profile-hero__chip-label">积分</span>
          <span class="profile-hero__chip-value">{{ points }}</span>
        </div>
        <div class="profile-hero__chip">
          <span class="profile-hero__chip-label">连学</span>
          <span class="profile-hero__chip-value">{{ studyStreak }}天</span>
        </div>
        <div class="profile-hero__chip">
          <span class="profile-hero__chip-label">连战</span>
          <span class="profile-hero__chip-value">{{ challengeStreak }}天</span>
        </div>
      </div>

      <div class="profile-hero__entry">
        <span class="profile-hero__entry-label">入卷时间</span>
        <span class="profile-hero__entry-value">{{ joinedDate }}</span>
      </div>

      <div class="profile-hero__actions">
        <button type="button" class="profile-hero__action profile-hero__action--primary" @click="$emit('navigateChallenge')">
          今日挑战
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type { UserInfo } from '@/api/user'
import type { UserStats } from '@/api/learning'
import UserAvatar from '@/components/UserAvatar.vue'
import { getRankByExp, getNextRank, getExpProgress } from '@/utils/levels'

const props = defineProps({
  user: {
    type: Object as PropType<UserInfo | null>,
    default: null
  },
  stats: {
    type: Object as PropType<UserStats | null>,
    default: null
  },
  challengeStreak: {
    type: Number,
    default: 0
  }
})

defineEmits<{
  navigateChallenge: []
  showRanks: []
}>()

const displayName = computed(() => props.user?.nickname || props.user?.username || '青衿旅人')
const safeUsername = computed(() => props.user?.username || 'qingjinfu')
const displayBio = computed(() => props.user?.bio || '把每一次阅读、每一回填词、每一缕灵感，都收进自己的诗心卷轴。')
const currentExp = computed(() => props.stats?.exp || props.user?.exp || 0)
const rankInfo = computed(() => getRankByExp(currentExp.value))
const currentLevel = computed(() => rankInfo.value.level)
const nextLevelExp = computed(() => nextRankInfo.value?.expRequired || currentExp.value)
const progressPercentage = computed(() => Math.min(100, Math.max(6, expProgress.value.percent)))
const points = computed(() => props.user?.points || 0)
const studyStreak = computed(() => props.stats?.streak_days || 0)

const nextRankInfo = computed(() => getNextRank(currentLevel.value))
const expProgress = computed(() => getExpProgress(currentExp.value))

const levelTitle = computed(() => rankInfo.value.name)

const progressText = computed(() => {
  if (!nextRankInfo.value) return '已至最高境界'
  const remain = nextRankInfo.value.expRequired - currentExp.value
  return `距「${nextRankInfo.value.name}」还需 ${Math.max(0, remain)} 点文采`
})

const joinedDate = computed(() => {
  if (!props.user?.created_at) return '今日入卷'
  const date = new Date(props.user.created_at)
  if (Number.isNaN(date.getTime())) return '今日入卷'
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
})
</script>

<style scoped>
.profile-hero {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 22px;
  min-height: 100%;
  height: 100%;
  padding: 32px 30px;
  border-radius: 32px;
  background:
    radial-gradient(circle at top left, rgba(217, 119, 87, 0.12), transparent 34%),
    radial-gradient(circle at bottom right, rgba(120, 140, 93, 0.1), transparent 42%),
    linear-gradient(180deg, rgba(250, 249, 245, 0.98), rgba(244, 240, 232, 0.94));
  border: 1px solid rgba(176, 174, 165, 0.18);
  box-shadow: 0 16px 34px rgba(94, 82, 72, 0.08);
  backdrop-filter: blur(16px);
}

.profile-hero::before,
.profile-hero::after {
  content: '';
  position: absolute;
  inset: 14px;
  border-radius: 24px;
  pointer-events: none;
}

.profile-hero::before {
  border: 1px solid rgba(176, 174, 165, 0.14);
  opacity: 0.9;
}

.profile-hero::after {
  inset: auto 16px 16px;
  height: 150px;
  background:
    linear-gradient(180deg, transparent, rgba(217, 119, 87, 0.04)),
    radial-gradient(circle at left bottom, rgba(217, 119, 87, 0.1), transparent 58%);
}

.profile-hero__mist {
  position: absolute;
  width: 180px;
  height: 180px;
  border-radius: 999px;
  filter: blur(36px);
  opacity: 0.28;
  pointer-events: none;
}

.profile-hero__mist--top {
  top: -50px;
  right: -30px;
  background: rgba(217, 119, 87, 0.22);
}

.profile-hero__mist--bottom {
  bottom: -60px;
  left: -40px;
  background: rgba(120, 140, 93, 0.18);
}

.profile-hero__identity-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.profile-hero__seal {
  position: relative;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(217, 119, 87, 0.2);
  color: #d97757;
  border-radius: 999px;
  font-family: var(--font-poem);
  font-size: 0.76rem;
  letter-spacing: 0.14em;
  background: rgba(255, 247, 244, 0.88);
  box-shadow: 0 6px 14px rgba(217, 119, 87, 0.08);
  transform: rotate(0deg);
}

.profile-hero__main {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.22fr) minmax(260px, 0.78fr);
  gap: 20px;
  align-items: start;
}

.profile-hero__identity-block {
  display: flex;
  align-items: flex-start;
  gap: 22px;
  min-width: 0;
}

.profile-hero__avatar-shell {
  position: relative;
  width: 110px;
  height: 110px;
  flex: 0 0 auto;
}

.profile-hero__avatar-ring {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(217, 119, 87, 0.16), rgba(120, 140, 93, 0.18));
  box-shadow: 0 10px 22px rgba(126, 109, 94, 0.12);
}

.profile-hero__avatar-shell :deep(.user-avatar) {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  border: 4px solid rgba(253, 254, 254, 0.9);
  box-shadow: 0 10px 22px rgba(94, 82, 72, 0.1);
}

.profile-hero__identity {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.profile-hero__eyebrow {
  font-size: 0.8rem;
  font-family: var(--font-title);
  letter-spacing: 0.28em;
  color: #b0aea5;
  margin-bottom: 0;
}

.profile-hero__name {
  font-size: clamp(2.2rem, 5vw, 2.9rem);
  color: #342e29;
  margin-bottom: 10px;
  letter-spacing: 0.05em;
  line-height: 1.3;
  text-wrap: balance;
}

.profile-hero__username {
  font-size: 0.92rem;
  font-family: var(--font-title);
  color: rgba(107, 98, 87, 0.66);
  margin-bottom: 16px;
  letter-spacing: 0.08em;
}

.profile-hero__bio {
  color: rgba(57, 50, 44, 0.72);
  line-height: 1.82;
  font-size: 0.97rem;
}

.profile-hero__growth {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 16px;
}

.profile-hero__rank-band {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(217, 119, 87, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(104, 90, 80, 0.95), rgba(136, 117, 101, 0.92));
  color: rgba(250, 249, 245, 0.96);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    0 8px 18px rgba(97, 84, 74, 0.12);
}

.profile-hero__rank-icon {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

.profile-hero__rank-level {
  font-size: 0.92rem;
  letter-spacing: 0.14em;
}

.profile-hero__rank-title {
  font-family: var(--font-poem);
  font-size: 1.15rem;
  letter-spacing: 0.22em;
}

.profile-hero__progress-block {
  position: relative;
  z-index: 1;
  padding: 20px 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(252, 250, 246, 0.88), rgba(246, 241, 234, 0.82));
  border: 1px solid rgba(176, 174, 165, 0.16);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.62),
    0 8px 16px rgba(94, 82, 72, 0.03);
}

.profile-hero__progress-meta,
.profile-hero__entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.profile-hero__progress-meta {
  color: rgba(57, 50, 44, 0.74);
  font-size: 0.92rem;
  margin-bottom: 12px;
}

.profile-hero__progress-track {
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(126, 109, 94, 0.12);
}

.profile-hero__progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #d97757, #cf8d6f, #788c5d);
  box-shadow: 0 4px 14px rgba(217, 119, 87, 0.16);
}

.profile-hero__progress-text {
  margin-top: 10px;
  font-size: 0.88rem;
  color: rgba(80, 75, 67, 0.68);
}

.profile-hero__footer {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(240px, 0.9fr);
  gap: 16px 16px;
  align-items: start;
}

.profile-hero__chips {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.profile-hero__chip {
  padding: 16px 12px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(252, 250, 246, 0.94), rgba(246, 241, 234, 0.88));
  border: 1px solid rgba(176, 174, 165, 0.16);
  text-align: center;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.62),
    0 8px 16px rgba(94, 82, 72, 0.03);
}

.profile-hero__chip-label {
  display: block;
  font-size: 0.8rem;
  font-family: var(--font-title);
  color: rgba(107, 98, 87, 0.66);
  margin-bottom: 8px;
  letter-spacing: 0.08em;
}

.profile-hero__chip-value {
  display: block;
  color: #342e29;
  font-weight: 700;
  font-size: 1rem;
}

.profile-hero__entry {
  position: relative;
  z-index: 1;
  grid-column: 2;
  padding: 16px 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(252, 250, 246, 0.9), rgba(246, 241, 234, 0.84));
  color: rgba(57, 50, 44, 0.72);
  border: 1px solid rgba(176, 174, 165, 0.16);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.56),
    0 8px 16px rgba(94, 82, 72, 0.03);
}

.profile-hero__entry-label {
  font-size: 0.9rem;
}

.profile-hero__entry-value {
  font-size: 0.9rem;
}

.profile-hero__actions {
  position: relative;
  z-index: 1;
  display: flex;
  grid-column: 1 / -1;
  justify-content: center;
  gap: 12px;
  padding-top: 2px;
}

.profile-hero__action {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 1 280px;
  min-width: 220px;
  min-height: 50px;
  padding: 0 18px;
  border: 1px solid transparent;
  border-radius: 18px;
  font-family: var(--font-body);
  font-size: 0.92rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  transition:
    transform var(--transition-normal),
    box-shadow var(--transition-normal),
    background var(--transition-normal),
    color var(--transition-normal),
    border-color var(--transition-normal);
}

.profile-hero__action::before {
  content: '';
  position: absolute;
  inset: 6px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  pointer-events: none;
}

.profile-hero__action:hover {
  transform: translateY(-2px);
}

.profile-hero__action--primary {
  background: linear-gradient(135deg, #d97757, #c86445);
  color: rgba(250, 249, 245, 0.96);
  box-shadow: 0 12px 22px rgba(217, 119, 87, 0.18);
}

@media (max-width: 1180px) {
  .profile-hero__main,
  .profile-hero__footer {
    grid-template-columns: minmax(0, 1fr);
  }

  .profile-hero__entry {
    grid-column: auto;
  }
}

@media (max-width: 960px) {
  .profile-hero {
    padding: 30px 22px;
  }

  .profile-hero__identity-block {
    flex-direction: column;
    gap: 18px;
  }
}

@media (max-width: 640px) {
  .profile-hero__actions {
    flex-direction: column;
  }

  .profile-hero__action {
    width: 100%;
    min-width: 0;
  }

  .profile-hero__chips {
    grid-template-columns: minmax(0, 1fr);
  }

  .profile-hero__name {
    font-size: 1.8rem;
  }
}
</style>
