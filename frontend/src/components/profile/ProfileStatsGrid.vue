<template>
  <section class="profile-stats-grid">
    <article
      v-for="item in items"
      :key="item.label"
      class="profile-stat"
      :class="`profile-stat--${item.accent}`"
    >
      <div class="profile-stat__glyph">{{ item.glyph }}</div>
      <div class="profile-stat__meta">
        <p class="profile-stat__label">{{ item.label }}</p>
        <div class="profile-stat__value">{{ item.value }}</div>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
interface ProfileStatItem {
  label: string
  value: string
  glyph: string
  accent: 'vermillion' | 'jade' | 'ink' | 'gold'
}

defineProps<{
  items: ProfileStatItem[]
}>()
</script>

<style scoped>
.profile-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.profile-stat {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  min-height: 124px;
  padding: 16px 15px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(252, 250, 246, 0.96), rgba(245, 240, 233, 0.9));
  border: 1px solid rgba(176, 174, 165, 0.16);
  box-shadow: 0 8px 18px rgba(94, 82, 72, 0.04);
  isolation: isolate;
}

.profile-stat::before {
  content: '';
  position: absolute;
  inset: 8px;
  border-radius: 16px;
  border: 1px solid rgba(176, 174, 165, 0.12);
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.3), transparent 56%),
    linear-gradient(0deg, rgba(255, 255, 255, 0.2), transparent 45%);
  pointer-events: none;
}

.profile-stat::after {
  content: '';
  position: absolute;
  right: -20px;
  bottom: -18px;
  width: 88px;
  height: 88px;
  border-radius: 999px;
  opacity: 0.16;
}

.profile-stat--vermillion::after {
  background: radial-gradient(circle, rgba(217, 119, 87, 0.34), transparent 72%);
}

.profile-stat--jade::after {
  background: radial-gradient(circle, rgba(120, 140, 93, 0.32), transparent 72%);
}

.profile-stat--ink::after {
  background: radial-gradient(circle, rgba(126, 109, 94, 0.3), transparent 72%);
}

.profile-stat--gold::after {
  background: radial-gradient(circle, rgba(158, 130, 69, 0.3), transparent 72%);
}

.profile-stat__glyph {
  position: relative;
  z-index: 1;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  font-family: var(--font-poem);
  font-size: 1.12rem;
  letter-spacing: 0.14em;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.34);
}

.profile-stat--vermillion .profile-stat__glyph {
  color: #d97757;
  background: rgba(217, 119, 87, 0.12);
}

.profile-stat--jade .profile-stat__glyph {
  color: #788c5d;
  background: rgba(120, 140, 93, 0.14);
}

.profile-stat--ink .profile-stat__glyph {
  color: #4d4239;
  background: rgba(126, 109, 94, 0.12);
}

.profile-stat--gold .profile-stat__glyph {
  color: #9e8245;
  background: rgba(158, 130, 69, 0.14);
}

.profile-stat__meta {
  position: relative;
  z-index: 1;
}

.profile-stat__label {
  margin-bottom: 6px;
  font-size: 0.78rem;
  font-family: var(--font-title);
  letter-spacing: 0.08em;
  color: rgba(107, 98, 87, 0.68);
}

.profile-stat__value {
  margin-bottom: 8px;
  color: #342e29;
  font-family: var(--font-title);
  font-size: clamp(1.3rem, 1.8vw, 1.66rem);
  line-height: 1.1;
  letter-spacing: 0.04em;
  text-wrap: balance;
}

@media (max-width: 980px) {
  .profile-stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .profile-stats-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .profile-stat {
    min-height: auto;
    grid-template-columns: 54px minmax(0, 1fr);
  }
}
</style>
