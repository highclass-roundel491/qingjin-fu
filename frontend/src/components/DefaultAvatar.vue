<template>
  <svg :width="svgSize" :height="svgSize" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient :id="gradientId" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" :style="{ stopColor: colors[0] }" />
        <stop offset="50%" :style="{ stopColor: colors[1] }" />
        <stop offset="100%" :style="{ stopColor: colors[2] }" />
      </linearGradient>
      
      <filter :id="filterId">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" result="noise" />
        <feColorMatrix in="noise" type="saturate" values="0" />
        <feBlend in="SourceGraphic" in2="noise" mode="multiply" />
      </filter>

      <pattern :id="patternId" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
        <circle cx="2" cy="2" r="0.5" :fill="colors[0]" opacity="0.1" />
        <circle cx="12" cy="12" r="0.5" :fill="colors[1]" opacity="0.1" />
      </pattern>
    </defs>

    <g class="avatar-container">
      <circle cx="60" cy="60" r="54" :fill="`url(#${gradientId})`" opacity="0.95" />
      
      <circle cx="60" cy="60" r="54" :fill="`url(#${patternId})`" />
      
      <path 
        d="M 60 6 L 65 15 L 75 15 L 67 22 L 70 32 L 60 26 L 50 32 L 53 22 L 45 15 L 55 15 Z"
        :fill="colors[2]"
        opacity="0.15"
      />
      
      <path 
        d="M 60 88 L 65 97 L 75 97 L 67 104 L 70 114 L 60 108 L 50 114 L 53 104 L 45 97 L 55 97 Z"
        :fill="colors[0]"
        opacity="0.15"
      />

      <circle cx="60" cy="60" r="54" fill="none" :stroke="colors[2]" stroke-width="0.5" opacity="0.3" />
      <circle cx="60" cy="60" r="48" fill="none" :stroke="colors[0]" stroke-width="0.3" opacity="0.2" />
      
      <text
        x="60"
        y="60"
        text-anchor="middle"
        dominant-baseline="central"
        :font-size="fontSize"
        fill="white"
        font-weight="500"
        font-family="'STKaiti', 'KaiTi', 'SimSun', serif"
        letter-spacing="2"
        :filter="`url(#${filterId})`"
      >
        {{ displayText }}
      </text>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  username: string
  size?: 'small' | 'medium' | 'large'
}

type AvatarPalette = [string, string, string]

const props = withDefaults(defineProps<Props>(), {
  size: 'medium'
})

const colorPalettes: AvatarPalette[] = [
  ['#c0392b', '#8b0000', '#d35400'],
  ['#16a085', '#0e6655', '#1abc9c'],
  ['#2c3e50', '#34495e', '#7f8c8d'],
  ['#8e44ad', '#5b2c6f', '#9b59b6'],
  ['#d35400', '#a04000', '#e67e22'],
  ['#27ae60', '#1e8449', '#52be80'],
  ['#2980b9', '#1a5276', '#5dade2'],
  ['#c0392b', '#922b21', '#e74c3c'],
  ['#f39c12', '#b9770e', '#f8c471'],
  ['#7d3c98', '#512e5f', '#a569bd']
]

const defaultPalette = colorPalettes[0] as AvatarPalette

const svgSize = computed(() => {
  const sizes = { small: 36, medium: 44, large: 72 }
  return sizes[props.size]
})

const fontSize = computed(() => {
  const sizes = { small: 20, medium: 26, large: 38 }
  return sizes[props.size]
})

const displayText = computed(() => {
  if (!props.username) return '?'
  const firstChar = props.username.charAt(0).toUpperCase()
  return /[\u4e00-\u9fa5]/.test(firstChar) ? firstChar : firstChar
})

const colors = computed<AvatarPalette>(() => {
  const hash = props.username.split('').reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc)
  }, 0)
  const index = Math.abs(hash) % colorPalettes.length
  return colorPalettes[index] ?? defaultPalette
})

const gradientId = computed(() => `gradient-${Math.random().toString(36).substr(2, 9)}`)
const filterId = computed(() => `filter-${Math.random().toString(36).substr(2, 9)}`)
const patternId = computed(() => `pattern-${Math.random().toString(36).substr(2, 9)}`)
</script>
