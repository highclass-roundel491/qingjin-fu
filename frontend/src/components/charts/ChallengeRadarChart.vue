<template>
  <div class="challenge-radar-chart">
    <div class="chart-header">
      <h3>挑战表现</h3>
      <span class="chart-subtitle">每日挑战综合评分</span>
    </div>
    <v-chart :option="chartOption" autoresize class="chart-container" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent
} from 'echarts/components'
import type { EChartsOption } from 'echarts'

use([
  CanvasRenderer,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent
])

interface Props {
  data: {
    beauty_avg: number
    creativity_avg: number
    mood_avg: number
  }
}

const props = defineProps<Props>()

const chartOption = computed<EChartsOption>(() => {
  
  return {
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: [
        { name: '意境美', max: 100 },
        { name: '创意度', max: 100 },
        { name: '情感分', max: 100 }
      ],
      shape: 'circle',
      splitNumber: 5,
      axisName: {
        color: '#2C3E50',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: ['#E0E0E0', '#E8E8E8', '#F0F0F0', '#F5F5F5', '#FAFAFA']
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(44, 62, 80, 0.05)', 'rgba(44, 62, 80, 0.02)']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#E0E0E0'
        }
      }
    },
    series: [
      {
        name: '挑战评分',
        type: 'radar',
        data: [
          {
            value: [
              props.data.beauty_avg,
              props.data.creativity_avg,
              props.data.mood_avg
            ],
            name: '平均分',
            areaStyle: {
              color: 'rgba(192, 57, 43, 0.3)'
            },
            lineStyle: {
              width: 3,
              color: '#C0392B'
            },
            itemStyle: {
              color: '#C0392B'
            }
          }
        ]
      }
    ]
  }
})
</script>

<style scoped>
.challenge-radar-chart {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: bold;
  color: #2C3E50;
  font-family: 'STKaiti', 'KaiTi', serif;
}

.chart-subtitle {
  font-size: 12px;
  color: #7F8C8D;
}

.chart-container {
  flex: 1;
  min-height: 280px;
}
</style>
