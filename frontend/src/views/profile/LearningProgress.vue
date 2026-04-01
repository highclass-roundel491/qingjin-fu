<template>
  <div class="learning-progress">
    <div v-if="loading" class="progress-loading">
      <div class="loading-spinner"></div>
      <p>加载学习数据中...</p>
    </div>

    <div v-else-if="error" class="progress-error">
      <div class="error-icon">⚠</div>
      <p>{{ error }}</p>
      <button @click="loadProgress" class="retry-button">重新加载</button>
    </div>

    <div v-else class="progress-content">
      <div class="progress-header">
        <div class="header-seal">进</div>
        <div class="header-text">
          <h2>学习进度</h2>
          <p>你的诗词研习轨迹与成长历程</p>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-card chart-card--wide">
          <StudyTimeChart v-if="progressData.daily_study_time.length" :data="progressData.daily_study_time" />
          <div v-else class="chart-empty">
            <p>暂无学习时长数据</p>
            <span>去诗词学堂开始学习吧</span>
          </div>
        </div>

        <div class="chart-card chart-card--wide">
          <CumulativeChart v-if="progressData.cumulative_learned.length" :data="progressData.cumulative_learned" />
          <div v-else class="chart-empty">
            <p>暂无累计学习数据</p>
            <span>学习诗词后这里会展示你的成长曲线</span>
          </div>
        </div>

        <div class="chart-card">
          <DynastyDistributionChart v-if="progressData.dynasty_distribution.length" :data="progressData.dynasty_distribution" />
          <div v-else class="chart-empty">
            <p>暂无朝代分布数据</p>
            <span>学习不同朝代的诗词</span>
          </div>
        </div>

        <div class="chart-card">
          <ChallengeRadarChart 
            v-if="hasChallenge" 
            :data="progressData.challenge_performance" 
          />
          <div v-else class="chart-empty">
            <p>暂无挑战数据</p>
            <span>去妙笔挑战自己</span>
          </div>
        </div>
      </div>

      <div v-if="progressData.genre_distribution.length" class="genre-list">
        <h3 class="genre-title">
          <span class="genre-seal">体</span>
          诗词体裁分布
        </h3>
        <div class="genre-items">
          <div 
            v-for="item in progressData.genre_distribution" 
            :key="item.genre"
            class="genre-item"
          >
            <span class="genre-name">{{ item.genre }}</span>
            <div class="genre-bar">
              <div 
                class="genre-bar-fill" 
                :style="{ width: `${(item.count / maxGenreCount) * 100}%` }"
              ></div>
            </div>
            <span class="genre-count">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { learningApi, type LearningProgress as LearningProgressData } from '@/api/learning'
import StudyTimeChart from '@/components/charts/StudyTimeChart.vue'
import CumulativeChart from '@/components/charts/CumulativeChart.vue'
import DynastyDistributionChart from '@/components/charts/DynastyDistributionChart.vue'
import ChallengeRadarChart from '@/components/charts/ChallengeRadarChart.vue'

const loading = ref(true)
const error = ref('')
const progressData = ref<LearningProgressData>({
  daily_study_time: [],
  dynasty_distribution: [],
  genre_distribution: [],
  cumulative_learned: [],
  challenge_performance: {
    beauty_avg: 0,
    creativity_avg: 0,
    mood_avg: 0
  },
  study_calendar: []
})

const hasChallenge = computed(() => {
  const perf = progressData.value.challenge_performance
  return perf.beauty_avg > 0 || perf.creativity_avg > 0 || perf.mood_avg > 0
})

const maxGenreCount = computed(() => {
  if (!progressData.value.genre_distribution.length) return 1
  return Math.max(...progressData.value.genre_distribution.map(item => item.count))
})

const loadProgress = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const data = await learningApi.getProgress()
    progressData.value = data
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载学习进度失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProgress()
})
</script>

<style scoped>
.learning-progress {
  min-height: 400px;
}

.progress-loading,
.progress-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #7F8C8D;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #E0E0E0;
  border-top-color: #C0392B;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-loading p {
  margin-top: 16px;
  font-size: 14px;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.progress-error p {
  margin-bottom: 16px;
  font-size: 14px;
}

.retry-button {
  padding: 8px 24px;
  background: #C0392B;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.retry-button:hover {
  background: #A93226;
  transform: translateY(-2px);
}

.progress-content {
  animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(44, 62, 80, 0.05) 0%, rgba(22, 160, 133, 0.05) 100%);
  border-radius: 12px;
  border: 1px solid rgba(44, 62, 80, 0.1);
}

.header-seal {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #C0392B 0%, #E74C3C 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  font-family: 'STKaiti', 'KaiTi', serif;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(192, 57, 43, 0.3);
}

.header-text h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: bold;
  color: #2C3E50;
  font-family: 'STKaiti', 'KaiTi', serif;
}

.header-text p {
  margin: 0;
  font-size: 14px;
  color: #7F8C8D;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
}

.chart-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.chart-card--wide {
  grid-column: span 2;
}

.chart-empty {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #95A5A6;
}

.chart-empty p {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
}

.chart-empty span {
  font-size: 14px;
  color: #BDC3C7;
}

.genre-list {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.genre-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 24px 0;
  font-size: 18px;
  font-weight: bold;
  color: #2C3E50;
  font-family: 'STKaiti', 'KaiTi', serif;
}

.genre-seal {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #16A085 0%, #1ABC9C 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(22, 160, 133, 0.3);
}

.genre-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.genre-item {
  display: grid;
  grid-template-columns: 120px 1fr 60px;
  align-items: center;
  gap: 16px;
}

.genre-name {
  font-size: 14px;
  color: #2C3E50;
  font-weight: 500;
}

.genre-bar {
  height: 24px;
  background: #ECF0F1;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.genre-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #16A085 0%, #1ABC9C 100%);
  border-radius: 12px;
  transition: width 0.6s ease;
}

.genre-count {
  text-align: right;
  font-size: 14px;
  color: #7F8C8D;
  font-weight: 500;
}

@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-card--wide {
    grid-column: span 1;
  }
}
</style>
