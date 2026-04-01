<template>
  <div class="games-hub">
    <div class="games-hub__deco games-hub__deco--left"></div>
    <div class="games-hub__deco games-hub__deco--right"></div>

    <div class="games-hub__nav">
      <router-link to="/" class="games-hub__back">← 返回首页</router-link>
    </div>

    <div class="games-hub__header">
      <h1 class="games-hub__title">互动游戏</h1>
      <p class="games-hub__subtitle">以诗会友 · 寓教于乐</p>
      <div v-if="userStore.isLogin && userStore.userInfo" class="games-hub__rank">
        <UserRank :level="userStore.userInfo.level" :exp="userStore.userInfo.exp" compact clickable @click="rankVisible = true" />
      </div>
    </div>

    <div class="games-hub__grid">
      <router-link to="/games/feihualing" class="game-card game-card--feihualing" style="animation-delay: 0s">
        <img :src="feihualingIcon" class="game-card__icon" alt="" />
        <div class="game-card__info">
          <div class="game-card__name">飞花令</div>
          <div class="game-card__desc">选定令字，限时吟诵含该字的诗句，连续闯关挑战诗词储备</div>
          <div class="game-card__footer">
            <span class="game-card__tag">单人闯关</span>
            <span class="game-card__meta">三级难度 · 30秒限时</span>
          </div>
        </div>
      </router-link>

      <router-link to="/relay" class="game-card game-card--relay" style="animation-delay: 0.1s">
        <img :src="relayIcon" class="game-card__icon" alt="" />
        <div class="game-card__info">
          <div class="game-card__name">诗词接龙</div>
          <div class="game-card__desc">以上句末字为下句首字，接续不断，比拼诗词功底</div>
          <div class="game-card__footer">
            <span class="game-card__tag">多人对弈</span>
            <span class="game-card__meta">实时匹配 · 排行榜</span>
          </div>
        </div>
      </router-link>

      <router-link to="/games/timed" class="game-card game-card--timed" style="animation-delay: 0.2s">
        <img :src="timedIcon" class="game-card__icon" alt="" />
        <div class="game-card__info">
          <div class="game-card__name">限时挑战</div>
          <div class="game-card__desc">随机出题，限时作答，考验你的诗词储备与反应速度</div>
          <div class="game-card__footer">
            <span class="game-card__tag">知识问答</span>
            <span class="game-card__meta">三级难度 · 连击加分</span>
          </div>
        </div>
      </router-link>
    </div>
  </div>

  <RankOverview
    v-if="userStore.isLogin && userStore.userInfo"
    v-model:visible="rankVisible"
    :current-level="userStore.userInfo.level"
    :current-exp="userStore.userInfo.exp"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import feihualingIcon from '@/assets/icons/games/feihualing-card.svg'
import relayIcon from '@/assets/icons/games/relay-card.svg'
import timedIcon from '@/assets/icons/games/timed-card.svg'
import UserRank from '@/components/UserRank.vue'
import RankOverview from '@/components/RankOverview.vue'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const rankVisible = ref(false)
</script>

<style>
@import './styles/games-hub.css';
</style>
