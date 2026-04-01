<template>
  <div class="user-rank" :class="['user-rank--' + rank.key, { 'user-rank--compact': compact, 'user-rank--clickable': clickable }]" @click="handleClick">
    <img :src="rank.icon" class="user-rank__icon" alt="" />
    <div class="user-rank__info" v-if="!compact">
      <div class="user-rank__name" :style="{ color: rank.color }">{{ rank.name }}</div>
      <div class="user-rank__desc">{{ rank.desc }}</div>
      <div class="user-rank__bar" v-if="showBar">
        <div class="user-rank__bar-fill" :style="{ width: progress.percent + '%', background: rank.color }"></div>
      </div>
      <div class="user-rank__exp" v-if="showBar && nextRank">
        {{ progress.current }} / {{ progress.total }}
      </div>
      <div class="user-rank__exp" v-else-if="showBar">
        已满级
      </div>
    </div>
    <span class="user-rank__badge" v-if="compact" :style="{ color: rank.color }">{{ rank.name }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getRankByExp, getRankByLevel, getNextRank, getExpProgress, type RankInfo } from '@/utils/levels'

const props = withDefaults(defineProps<{
  level: number
  exp?: number
  compact?: boolean
  showBar?: boolean
  clickable?: boolean
}>(), {
  compact: false,
  showBar: false,
  clickable: false
})

const emit = defineEmits<{
  click: []
}>()

const rank = computed<RankInfo>(() => typeof props.exp === 'number' ? getRankByExp(props.exp) : getRankByLevel(props.level))
const nextRank = computed(() => getNextRank(rank.value.level))
const progress = computed(() => getExpProgress(typeof props.exp === 'number' ? props.exp : rank.value.expRequired))

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped>
.user-rank {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-rank--compact {
  gap: 4px;
}

.user-rank--clickable {
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.user-rank--clickable:hover {
  opacity: 0.75;
}

.user-rank__icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.user-rank--compact .user-rank__icon {
  width: 20px;
  height: 20px;
}

.user-rank__info {
  flex: 1;
  min-width: 0;
}

.user-rank__name {
  font-family: var(--font-title);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
}

.user-rank__desc {
  font-size: 12px;
  color: var(--color-ink-medium);
  opacity: 0.6;
  margin-top: 2px;
}

.user-rank__bar {
  margin-top: 6px;
  height: 4px;
  background: rgba(18, 17, 16, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.user-rank__bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}

.user-rank__exp {
  font-size: 11px;
  color: var(--color-ink-medium);
  opacity: 0.5;
  margin-top: 2px;
}

.user-rank__badge {
  font-family: var(--font-title);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
}
</style>
