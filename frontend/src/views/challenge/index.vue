<template>
  <div class="miaobi-page">
    <div class="miaobi-bg"></div>
    <img :src="cloudDecoration" class="miaobi-deco miaobi-deco--cloud" alt="" />
    <img :src="brushDecoration" class="miaobi-deco miaobi-deco--brush" alt="" />
    <img :src="lotusDecoration" class="miaobi-deco miaobi-deco--lotus" alt="" />

    <div class="miaobi-container">
      <header class="miaobi-header">
        <div class="header-left">
          <h1 class="page-title">妙笔</h1>
          <p class="page-subtitle">妙笔生花，以字入诗</p>
        </div>
        <div class="header-right">
          <router-link to="/challenge/rankings" class="header-ranking-link">排行榜</router-link>
          <div v-if="userStore.isLogin" class="header-growth">
            <span class="header-growth__label">当前卷阶</span>
            <strong class="header-growth__value">Lv.{{ currentLevel }} · {{ currentExp }} 文采</strong>
          </div>
          <div v-if="streakDays > 0" class="streak-pill">
            <span class="streak-flame"></span>
            <span class="streak-text">连续 {{ streakDays }} 天</span>
          </div>
        </div>
      </header>

      <nav class="tab-nav">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <span class="tab-mark">{{ tab.mark }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </nav>

      <div v-if="loading" class="loading-state">
        <div class="loading-brush"></div>
        <p>正在研墨...</p>
      </div>

      <div v-else class="miaobi-workspace">
        <aside class="miaobi-sidebar">
          <article class="side-card side-card--growth">
            <div class="side-card__eyebrow">GROWTH LEDGER</div>
            <h3 class="side-card__title">文采与卷阶</h3>
            <p class="side-card__text">{{ growthNotice }}</p>
            <UserRank v-if="userStore.isLogin" :level="currentLevel" :exp="currentExp" :show-bar="true" class="side-rank" />
            <div v-else class="side-login-hint">登录后即可记录妙笔经验与积分，并同步到个人中心。</div>
            <div class="side-stats">
              <div class="side-stat">
                <span>当前文采</span>
                <strong>{{ currentExp }}</strong>
              </div>
              <div class="side-stat">
                <span>累计积分</span>
                <strong>{{ currentPoints }}</strong>
              </div>
              <div class="side-stat">
                <span>连战天数</span>
                <strong>{{ streakDays }}天</strong>
              </div>
            </div>
            <button class="side-link" @click="goProfile">
              <span>查看个人中心</span>
              <ArrowRightIcon class="side-link__icon" />
            </button>
          </article>

          <article class="side-card side-card--focus">
            <div class="side-card__eyebrow">{{ activeTabMeta.eyebrow }}</div>
            <h3 class="side-card__title">{{ activeTabMeta.title }}</h3>
            <p class="side-card__text">{{ activeTabMeta.desc }}</p>
            <div class="side-stat side-stat--highlight">
              <span>{{ sidebarSummary.label }}</span>
              <strong>{{ sidebarSummary.value }}</strong>
            </div>
            <div class="side-actions">
              <button class="side-action side-action--primary" @click="handlePrimaryAction">{{ activeTabMeta.actionText }}</button>
              <button class="side-action side-action--secondary" @click="goChallengeCreate">{{ activeTab === 'create' ? '前往题场' : '我来出题' }}</button>
            </div>
          </article>
        </aside>

        <div class="miaobi-content">
          <section v-if="activeTab === 'daily'" class="tab-panel">
            <div v-if="dailyChallenge" class="daily-section">
              <div class="daily-card">
                <div class="card-seal">今</div>
                <div class="card-header">
                  <div class="card-date">{{ formatDate(dailyChallenge.date) }}</div>
                  <div class="card-tags">
                    <span v-if="dailyChallenge.theme" class="tag">{{ dailyChallenge.theme }}</span>
                    <span v-if="dailyChallenge.mood" class="tag mood">{{ dailyChallenge.mood }}</span>
                  </div>
                </div>

                <div class="poem-canvas">
                  <div class="poem-row">
                    <span class="poem-char" v-for="(c, i) in parts1.before" :key="'b1'+i">{{ c }}</span>
                    <span class="blank-mark">(</span>
                    <input
                      v-model="answer1"
                      type="text"
                      :maxlength="dailyChallenge.blank_count"
                      class="blank-input"
                      :disabled="dailySubmitted"
                      @keyup.enter="submitDaily"
                      :placeholder="blankPlaceholder"
                    />
                    <span class="blank-mark">)</span>
                    <span class="poem-char" v-for="(c, i) in parts1.after" :key="'a1'+i">{{ c }}</span>
                  </div>
                  <div v-if="dailyChallenge.sentence_template_2" class="poem-row">
                    <span class="poem-char" v-for="(c, i) in parts2.before" :key="'b2'+i">{{ c }}</span>
                    <span class="blank-mark">(</span>
                    <input
                      v-model="answer2"
                      type="text"
                      :maxlength="dailyChallenge.blank_count"
                      class="blank-input"
                      :disabled="dailySubmitted"
                      @keyup.enter="submitDaily"
                      :placeholder="blankPlaceholder"
                    />
                    <span class="blank-mark">)</span>
                    <span class="poem-char" v-for="(c, i) in parts2.after" :key="'a2'+i">{{ c }}</span>
                  </div>
                </div>

                <div v-if="dailyChallenge.hint && !dailySubmitted" class="hint-strip">
                  <span class="hint-label">出题者填字</span>
                  <span class="hint-content">{{ dailyChallenge.hint }}</span>
                </div>

                <div v-if="!dailySubmitted" class="ai-hint-area">
                  <div v-if="dailyHintText" class="ai-hint-bubble">{{ dailyHintText }}</div>
                  <button
                    v-if="dailyHintNextAvailable"
                    class="btn-ai-hint"
                    :disabled="dailyHintLoading"
                    @click="requestDailyHint"
                  >{{ dailyHintLoading ? '思索中...' : dailyHintLevel === 0 ? 'AI 提示' : '更深提示' }}</button>
                  <AiPhaseStatus
                    v-if="dailyHintLoading"
                    title="翰林提示推演中"
                    :stages="hintStages"
                    :current="dailyHintStep"
                    hint="提示层级越深，信息越接近答案"
                    :dense="true"
                  />
                </div>

                <button
                  v-if="!dailySubmitted"
                  class="btn-luobi"
                  :disabled="!canSubmitDaily || dailySubmitting"
                  @click="submitDaily"
                >{{ dailySubmitting ? 'AI 品鉴中...' : '落笔' }}</button>

                <div v-if="dailySubmitted && dailyResult" class="result-reveal">
                  <div class="result-tag">落笔成诗</div>
                  <div class="result-poem-text">{{ dailyResult.completed_sentence }}</div>
                  <div v-if="dailyResult.completed_sentence_2" class="result-poem-text">{{ dailyResult.completed_sentence_2 }}</div>

                  <div v-if="dailyResult.ai_score > 0" class="ai-score-panel">
                    <div class="ai-score-header">
                      <span class="ai-score-label">AI 品鉴</span>
                      <span class="ai-score-total" :class="scoreGrade(dailyResult.ai_score)">{{ dailyResult.ai_score }} 分</span>
                    </div>
                    <div class="ai-score-bars">
                      <div class="score-bar-item">
                        <span class="score-bar-name">意境</span>
                        <div class="score-bar-track"><div class="score-bar-fill beauty" :style="{ width: (dailyResult.beauty_score / 30 * 100) + '%' }"></div></div>
                        <span class="score-bar-val">{{ dailyResult.beauty_score }}/30</span>
                      </div>
                      <div class="score-bar-item">
                        <span class="score-bar-name">创意</span>
                        <div class="score-bar-track"><div class="score-bar-fill creativity" :style="{ width: (dailyResult.creativity_score / 30 * 100) + '%' }"></div></div>
                        <span class="score-bar-val">{{ dailyResult.creativity_score }}/30</span>
                      </div>
                      <div class="score-bar-item">
                        <span class="score-bar-name">情感</span>
                        <div class="score-bar-track"><div class="score-bar-fill mood" :style="{ width: (dailyResult.mood_score / 30 * 100) + '%' }"></div></div>
                        <span class="score-bar-val">{{ dailyResult.mood_score }}/30</span>
                      </div>
                    </div>
                    <div v-if="dailyResult.ai_feedback" class="ai-feedback">{{ dailyResult.ai_feedback }}</div>
                    <div v-if="dailyResult.ai_highlight" class="ai-highlight">{{ dailyResult.ai_highlight }}</div>
                    <div v-if="dailyResult.is_original_match" class="ai-original-match">与原诗相合</div>
                  </div>

                  <div class="result-footer">
                    <span class="reward">+{{ dailyResult.exp_gained }} 经验</span>
                    <span class="reward">+{{ dailyResult.points_gained }} 积分</span>
                  </div>
                  <div class="ai-coming">本次落笔收益已同步到个人中心</div>
                  <div class="cross-links">
                    <router-link to="/poems" class="cross-link">去诗词课堂继续研读</router-link>
                    <router-link to="/games/feihualing" class="cross-link">飞花令对决</router-link>
                    <router-link to="/works/create" class="cross-link">去创作一首</router-link>
                  </div>
                </div>
              </div>

              <div class="responses-block">
                <div class="block-header">
                  <h3 class="block-title">众人妙笔</h3>
                  <button
                    v-if="dailyResponses.length >= 2"
                    class="btn-ai-review"
                    :disabled="dailyReviewLoading"
                    @click="requestDailyReview"
                  >{{ dailyReviewLoading ? '品鉴中...' : 'AI 赏析' }}</button>
                </div>
                <AiPhaseStatus
                  v-if="dailyReviewLoading"
                  title="翰林横向赏析中"
                  :stages="reviewStages"
                  :current="dailyReviewStep"
                  hint="正在比较不同作答的意境与用字"
                />
                <div v-if="dailyReviewData" class="ai-review-panel">
                  <div class="review-best">
                    <span class="review-best-label">妙笔之选</span>
                    <span class="review-best-reason">{{ dailyReviewData.best_reason }}</span>
                  </div>
                  <div v-if="dailyReviewData.answer_tags.length" class="review-tags">
                    <span v-for="(tag, i) in dailyReviewData.answer_tags" :key="i" class="review-tag">{{ tag }}</span>
                  </div>
                  <div class="review-text">{{ dailyReviewData.overall_review }}</div>
                  <div v-if="dailyReviewData.diversity_note" class="review-diversity">{{ dailyReviewData.diversity_note }}</div>
                </div>
                <div v-if="dailyResponses.length" class="responses-list">
                  <div v-for="(r, idx) in dailyResponses" :key="r.id" class="response-row" :class="{ 'is-best': dailyReviewData && dailyReviewData.best_answer_index === idx }">
                    <span class="resp-author">{{ r.username || '匿名' }}</span>
                    <span class="resp-answer">{{ r.answer }}</span>
                    <span class="resp-time">{{ formatTime(r.submitted_at) }}</span>
                  </div>
                </div>
                <div v-else class="empty-hint">尚无人落笔，你来开卷</div>
              </div>
            </div>

            <div v-else class="empty-daily">
              <div class="empty-icon-wrapper"><PenIcon class="empty-icon" /></div>
              <p>今日妙题尚未出炉</p>
              <p class="empty-sub">明日再来，或前往广场一试身手</p>
            </div>
          </section>

          <section v-else-if="activeTab === 'plaza'" class="tab-panel">
            <div v-if="plazaList.length" class="card-grid">
              <div
                v-for="c in plazaList" :key="c.id"
                class="puzzle-card"
                @click="openDetail(c)"
              >
                <div class="puzzle-preview">{{ previewTemplate(c.sentence_template) }}</div>
                <div v-if="c.sentence_template_2" class="puzzle-preview sub">{{ previewTemplate(c.sentence_template_2) }}</div>
                <div class="puzzle-footer">
                  <span class="puzzle-author">{{ c.creator_name || '系统出题' }}</span>
                  <span class="puzzle-count">{{ c.response_count }} 人落笔</span>
                  <button
                    v-if="userStore.userInfo && c.creator_id === userStore.userInfo.id"
                    class="puzzle-delete"
                    @click.stop="handleDeleteChallenge(c.id, 'plaza')"
                  >删除</button>
                </div>
              </div>
            </div>
            <div v-else class="empty-hint">
              <p>广场暂无题目</p>
              <button class="btn-go-create" @click="activeTab = 'create'">我来出题</button>
            </div>
          </section>

          <section v-else-if="activeTab === 'continue'" class="tab-panel">
            <div v-if="continueList.length" class="card-grid">
              <div
                v-for="c in continueList" :key="c.id"
                class="puzzle-card continue-card"
                @click="openDetail(c)"
              >
                <div class="puzzle-preview">{{ c.sentence_template }}</div>
                <div class="puzzle-footer">
                  <span class="puzzle-author">{{ c.creator_name || '系统出题' }}</span>
                  <span class="puzzle-count">{{ c.response_count }} 人续写</span>
                  <button
                    v-if="userStore.userInfo && c.creator_id === userStore.userInfo.id"
                    class="puzzle-delete"
                    @click.stop="handleDeleteChallenge(c.id, 'continue')"
                  >删除</button>
                </div>
              </div>
            </div>
            <div v-else class="empty-hint">
              <p>尚无续写题目</p>
              <button class="btn-go-create" @click="activeTab = 'create'">我来起句</button>
            </div>
          </section>

          <section v-else class="tab-panel">
            <div class="create-form-card">
              <div class="form-title-row">
                <h3 class="form-title">出题台</h3>
              </div>

              <div class="form-field">
                <label>出题类型</label>
                <div class="type-toggle">
                  <button
                    :class="{ active: createForm.type === 'fill_blank' }"
                    @click="createForm.type = 'fill_blank'"
                  >填字挑战</button>
                  <button
                    :class="{ active: createForm.type === 'continue_line' }"
                    @click="createForm.type = 'continue_line'"
                  >续写接力</button>
                </div>
              </div>

              <template v-if="createForm.type === 'continue_line'">
                <div class="form-field">
                  <label>起始诗句</label>
                  <textarea
                    v-model="createForm.template"
                    placeholder="例：春江潮水连海平"
                    rows="2"
                    class="form-textarea"
                  ></textarea>
                </div>
              </template>

              <template v-else>
                <div class="form-field">
                  <label>上句（用 __ 标记留白处，必须与下句对仗）</label>
                  <textarea
                    v-model="createForm.template"
                    placeholder="例：山色湖光__鹤梦"
                    rows="2"
                    class="form-textarea"
                  ></textarea>
                </div>

                <div class="form-field">
                  <label>下句（用 __ 标记留白处，必须与上句对仗）</label>
                  <textarea
                    v-model="createForm.template2"
                    placeholder="例：月色水影__梅魂"
                    rows="2"
                    class="form-textarea"
                  ></textarea>
                </div>

                <div class="form-field">
                  <label>你的答案（出题者心中的标准答案，可选）</label>
                  <input v-model="createForm.hint" placeholder="上句答案,下句答案（如：伴,送）" class="form-input" />
                  <div class="form-hint">💡 发布前可用翰林品鉴进行检查</div>
                </div>

                <button
                  class="btn-ai-check"
                  :disabled="!createForm.template || !createForm.template2 || aiGenerating"
                  @click="handleAICheck"
                >
                  {{ aiGenerating ? '品鉴中...' : '翰林品鉴' }}
                </button>

                <AiPhaseStatus
                  v-if="aiGenerating"
                  title="翰林正在品鉴"
                  :stages="aiProgressSteps"
                  :current="aiCurrentStep"
                  hint="完成后会给出是否通过与修改建议"
                />

                <div v-if="aiCheckResult" class="ai-check-result">
                  <div class="check-result-header" :class="aiCheckResult.is_valid ? 'valid' : 'invalid'">
                    {{ aiCheckResult.is_valid ? '✓ 翰林赞许' : '⚠ 翰林批注' }}
                  </div>
                  <div class="check-feedback">{{ aiCheckResult.feedback }}</div>
                  <div v-if="aiCheckResult.suggestions && aiCheckResult.suggestions.length" class="check-suggestions">
                    <div class="check-suggestions-title">修改建议：</div>
                    <ul>
                      <li v-for="(s, i) in aiCheckResult.suggestions" :key="i">{{ s }}</li>
                    </ul>
                  </div>
                </div>
              </template>

              <button class="btn-publish" :disabled="!canCreate" @click="handleCreate">
                发布出题
              </button>
            </div>
          </section>

          <div v-if="detailChallenge" class="detail-overlay" @click.self="closeDetail">
            <div class="detail-panel">
              <button class="detail-close" @click="closeDetail">×</button>
              <div class="detail-type-tag">{{ detailChallenge.challenge_type === 'fill_blank' ? '填字' : '续写' }}</div>
              <div v-if="detailChallenge.creator_name" class="detail-creator">
                出题人：{{ detailChallenge.creator_name }}
                <button
                  v-if="userStore.userInfo && detailChallenge.creator_id === userStore.userInfo.id"
                  class="detail-delete-btn"
                  @click="handleDeleteDetailChallenge"
                >删除此题</button>
              </div>

              <div v-if="detailChallenge.challenge_type === 'fill_blank'" class="detail-poem-canvas">
                <div class="poem-canvas">
                  <div class="poem-row">
                    <span class="poem-char" v-for="(c, i) in detailParts1.before" :key="'db1'+i">{{ c }}</span>
                    <span class="blank-mark">(</span>
                    <input
                      v-model="detailAnswer1"
                      type="text"
                      :maxlength="detailChallenge.blank_count"
                      class="blank-input"
                      :disabled="detailSubmitted"
                      @keyup.enter="submitDetail"
                    />
                    <span class="blank-mark">)</span>
                    <span class="poem-char" v-for="(c, i) in detailParts1.after" :key="'da1'+i">{{ c }}</span>
                  </div>
                  <div v-if="detailChallenge.sentence_template_2" class="poem-row">
                    <span class="poem-char" v-for="(c, i) in detailParts2.before" :key="'db2'+i">{{ c }}</span>
                    <span class="blank-mark">(</span>
                    <input
                      v-model="detailAnswer2"
                      type="text"
                      :maxlength="detailChallenge.blank_count"
                      class="blank-input"
                      :disabled="detailSubmitted"
                      @keyup.enter="submitDetail"
                    />
                    <span class="blank-mark">)</span>
                    <span class="poem-char" v-for="(c, i) in detailParts2.after" :key="'da2'+i">{{ c }}</span>
                  </div>
                </div>
              </div>

              <div v-else class="detail-continue-area">
                <div class="continue-start-line">{{ detailChallenge.sentence_template }}</div>
                <textarea
                  v-model="detailContinueText"
                  class="continue-input"
                  :disabled="detailSubmitted"
                  placeholder="续写下句..."
                  rows="2"
                ></textarea>
              </div>

              <div v-if="detailChallenge.hint && !detailSubmitted" class="hint-strip">
                <span class="hint-label">出题者填字</span>
                <span class="hint-content">{{ detailChallenge.hint }}</span>
              </div>

              <div v-if="!detailSubmitted" class="ai-hint-area">
                <div v-if="detailHintText" class="ai-hint-bubble">{{ detailHintText }}</div>
                <button
                  v-if="detailHintNextAvailable"
                  class="btn-ai-hint"
                  :disabled="detailHintLoading"
                  @click="requestDetailHint"
                >{{ detailHintLoading ? '思索中...' : detailHintLevel === 0 ? 'AI 提示' : '更深提示' }}</button>
                <AiPhaseStatus
                  v-if="detailHintLoading"
                  title="翰林提示推演中"
                  :stages="hintStages"
                  :current="detailHintStep"
                  hint="已结合题面与诗句语境生成提示"
                  :dense="true"
                />
              </div>

              <button v-if="!detailSubmitted" class="btn-luobi" :disabled="!canSubmitDetail || detailSubmitting" @click="submitDetail">{{ detailSubmitting ? 'AI 品鉴中...' : '落笔' }}</button>

              <div v-if="detailSubmitted && detailResult" class="result-reveal compact">
                <div class="result-tag">落笔成诗</div>
                <div class="result-poem-text">{{ detailResult.completed_sentence }}</div>
                <div v-if="detailResult.completed_sentence_2" class="result-poem-text">{{ detailResult.completed_sentence_2 }}</div>

                <div v-if="detailResult.ai_score > 0" class="ai-score-panel">
                  <div class="ai-score-header">
                    <span class="ai-score-label">AI 品鉴</span>
                    <span class="ai-score-total" :class="scoreGrade(detailResult.ai_score)">{{ detailResult.ai_score }} 分</span>
                  </div>
                  <div class="ai-score-bars">
                    <div class="score-bar-item">
                      <span class="score-bar-name">意境</span>
                      <div class="score-bar-track"><div class="score-bar-fill beauty" :style="{ width: (detailResult.beauty_score / 30 * 100) + '%' }"></div></div>
                      <span class="score-bar-val">{{ detailResult.beauty_score }}/30</span>
                    </div>
                    <div class="score-bar-item">
                      <span class="score-bar-name">创意</span>
                      <div class="score-bar-track"><div class="score-bar-fill creativity" :style="{ width: (detailResult.creativity_score / 30 * 100) + '%' }"></div></div>
                      <span class="score-bar-val">{{ detailResult.creativity_score }}/30</span>
                    </div>
                    <div class="score-bar-item">
                      <span class="score-bar-name">情感</span>
                      <div class="score-bar-track"><div class="score-bar-fill mood" :style="{ width: (detailResult.mood_score / 30 * 100) + '%' }"></div></div>
                      <span class="score-bar-val">{{ detailResult.mood_score }}/30</span>
                    </div>
                  </div>
                  <div v-if="detailResult.ai_feedback" class="ai-feedback">{{ detailResult.ai_feedback }}</div>
                  <div v-if="detailResult.ai_highlight" class="ai-highlight">{{ detailResult.ai_highlight }}</div>
                  <div v-if="detailResult.is_original_match" class="ai-original-match">与原诗相合</div>
                </div>

                <div class="result-footer">
                  <span class="reward">+{{ detailResult.exp_gained }} 经验</span>
                  <span class="reward">+{{ detailResult.points_gained }} 积分</span>
                </div>
                <div class="cross-links">
                  <router-link to="/poems" class="cross-link">去诗词课堂研读</router-link>
                  <router-link to="/works/create" class="cross-link">去创作一首</router-link>
                </div>
              </div>

              <div class="detail-responses">
                <div class="block-header">
                  <h4>众人妙笔 ({{ detailResponses.length }})</h4>
                  <button
                    v-if="detailResponses.length >= 2"
                    class="btn-ai-review"
                    :disabled="detailReviewLoading"
                    @click="requestDetailReview"
                  >{{ detailReviewLoading ? '品鉴中...' : 'AI 赏析' }}</button>
                </div>
                <AiPhaseStatus
                  v-if="detailReviewLoading"
                  title="翰林横向赏析中"
                  :stages="reviewStages"
                  :current="detailReviewStep"
                  hint="正在提炼妙笔之选与整体点评"
                />
                <div v-if="detailReviewData" class="ai-review-panel">
                  <div class="review-best">
                    <span class="review-best-label">妙笔之选</span>
                    <span class="review-best-reason">{{ detailReviewData.best_reason }}</span>
                  </div>
                  <div v-if="detailReviewData.answer_tags.length" class="review-tags">
                    <span v-for="(tag, i) in detailReviewData.answer_tags" :key="'dt'+i" class="review-tag">{{ tag }}</span>
                  </div>
                  <div class="review-text">{{ detailReviewData.overall_review }}</div>
                  <div v-if="detailReviewData.diversity_note" class="review-diversity">{{ detailReviewData.diversity_note }}</div>
                </div>
                <div v-for="(r, idx) in detailResponses" :key="r.id" class="response-row" :class="{ 'is-best': detailReviewData && detailReviewData.best_answer_index === idx }">
                  <span class="resp-author">{{ r.username || '匿名' }}</span>
                  <span class="resp-answer">{{ r.answer }}{{ r.content ? ' / ' + r.content : '' }}</span>
                  <div class="resp-trail">
                    <span class="resp-time">{{ formatTime(r.submitted_at) }}</span>
                    <button
                      v-if="userStore.userInfo && r.user_id === userStore.userInfo.id"
                      class="resp-delete"
                      @click.stop="handleDeleteResponse(r.id)"
                    >删除</button>
                  </div>
                </div>
                <div v-if="!detailResponses.length" class="empty-hint small">暂无作答</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { challengeApi, type DailyChallenge, type ChallengeSubmitResponse, type ChallengeResponseItem, type ChallengeAIReviewResponse } from '@/api/challenge'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import UserRank from '@/components/UserRank.vue'
import AiPhaseStatus from '@/components/AiPhaseStatus.vue'
import { PenIcon, ArrowRightIcon } from '@/components/icons'
import { getRankByExp, getNextRank } from '@/utils/levels'
import cloudDecoration from '@/assets/icons/decorations/cloud.svg'
import brushDecoration from '@/assets/icons/decorations/brush.svg'
import lotusDecoration from '@/assets/icons/decorations/lotus.svg'

type TabKey = 'daily' | 'plaza' | 'continue' | 'create'

const router = useRouter()
const route = useRoute()

const tabs: Array<{ key: TabKey; label: string; mark: string }> = [
  { key: 'daily', label: '今日妙题', mark: '题' },
  { key: 'plaza', label: '填字广场', mark: '填' },
  { key: 'continue', label: '续写接力', mark: '续' },
  { key: 'create', label: '我来出题', mark: '出' },
]

const userStore = useUserStore()
const loading = ref(true)
const activeTab = ref<TabKey>('daily')
const streakDays = ref(0)

const dailyChallenge = ref<DailyChallenge | null>(null)
const answer1 = ref('')
const answer2 = ref('')
const dailySubmitted = ref(false)
const dailySubmitting = ref(false)
const dailyResult = ref<ChallengeSubmitResponse | null>(null)
const dailyResponses = ref<ChallengeResponseItem[]>([])

const plazaList = ref<DailyChallenge[]>([])
const continueList = ref<DailyChallenge[]>([])

const detailChallenge = ref<DailyChallenge | null>(null)
const detailAnswer1 = ref('')
const detailAnswer2 = ref('')
const detailContinueText = ref('')
const detailSubmitted = ref(false)
const detailSubmitting = ref(false)
const detailResult = ref<ChallengeSubmitResponse | null>(null)
const detailResponses = ref<ChallengeResponseItem[]>([])

const createForm = reactive({
  type: 'fill_blank' as 'fill_blank' | 'continue_line',
  template: '',
  template2: '',
  hint: '',
})

const aiCheckResult = ref<{
  is_valid: boolean
  feedback: string
  suggestions: string[]
} | null>(null)

const aiGenerating = ref(false)
const aiProgressSteps = ref(['验证诗句', '检查对仗', '分析格律', '生成意见'])
const aiCurrentStep = ref(0)
const dailyHintStep = ref(0)
const detailHintStep = ref(0)
const dailyReviewStep = ref(0)
const detailReviewStep = ref(0)

const hintStages = ['解析题面', '检索原诗', '生成提示']
const reviewStages = ['汇总作答', '比对原句', '生成赏析']

const createProgressTimer = ref<number | null>(null)
const dailyHintTimer = ref<number | null>(null)
const detailHintTimer = ref<number | null>(null)
const dailyReviewTimer = ref<number | null>(null)
const detailReviewTimer = ref<number | null>(null)

const clearPhaseTimer = (timerRef: { value: number | null }) => {
  if (timerRef.value !== null) {
    clearInterval(timerRef.value)
    timerRef.value = null
  }
}

const startPhaseLoop = (
  stageRef: { value: number },
  stages: string[],
  timerRef: { value: number | null },
  interval = 2200,
) => {
  clearPhaseTimer(timerRef)
  stageRef.value = 0
  timerRef.value = window.setInterval(() => {
    if (stageRef.value < stages.length - 1) {
      stageRef.value += 1
      return
    }
    clearPhaseTimer(timerRef)
  }, interval)
}

const currentExp = computed(() => userStore.userInfo?.exp || 0)
const currentLevel = computed(() => getRankByExp(currentExp.value).level)
const currentPoints = computed(() => userStore.userInfo?.points || 0)
const nextRankInfo = computed(() => getNextRank(currentLevel.value))

const growthNotice = computed(() => {
  if (!userStore.isLogin) return '登录后，你在妙笔中的每次落笔都会沉淀为经验与积分，并同步到个人中心。'
  if (!nextRankInfo.value) return '你已抵达当前最高卷阶，继续落笔会持续累积个人文采与妙笔履历。'
  const remain = Math.max(0, nextRankInfo.value.expRequired - currentExp.value)
  return `距「${nextRankInfo.value.name}」还差 ${remain} 点文采，妙笔收益会实时同步到个人中心。`
})

const activeTabMeta = computed(() => {
  if (activeTab.value === 'daily') {
    return {
      eyebrow: 'DAILY CANVAS',
      title: '今日妙题',
      desc: '聚焦今日题眼，在一题两句之间提炼自己的诗感与手感。',
      actionText: dailySubmitted.value ? '转去广场' : '立即落笔'
    }
  }
  if (activeTab.value === 'plaza') {
    return {
      eyebrow: 'FILL-BLANK PLAZA',
      title: '填字广场',
      desc: '浏览众人题面，择一题会友，看到不同笔意如何落在同一行句中。',
      actionText: '刷新题场'
    }
  }
  if (activeTab.value === 'continue') {
    return {
      eyebrow: 'RELAY STUDIO',
      title: '续写接力',
      desc: '顺着前句接住意脉，让一行诗继续生长。',
      actionText: '刷新续写'
    }
  }
  return {
    eyebrow: 'AUTHOR DESK',
    title: '我来出题',
    desc: '出一组对仗工整的上下句，挖空关键字（通常是动词），让后来者填字成诗。',
    actionText: '发布出题'
  }
})

const sidebarSummary = computed(() => {
  if (activeTab.value === 'daily') {
    return {
      label: '今日题眼',
      value: dailyChallenge.value?.theme || dailyChallenge.value?.mood || '自由落笔'
    }
  }
  if (activeTab.value === 'plaza') {
    return {
      label: '当前题数',
      value: `${plazaList.value.length} 题在场`
    }
  }
  if (activeTab.value === 'continue') {
    return {
      label: '待续长句',
      value: `${continueList.value.length} 题待续`
    }
  }
  return {
    label: '当前模式',
    value: createForm.type === 'fill_blank' ? '填字挑战' : '续写接力'
  }
})

const splitTemplate = (tmpl: string) => {
  const idx = tmpl.indexOf('__')
  if (idx === -1) return { before: tmpl, after: '' }
  return { before: tmpl.substring(0, idx), after: tmpl.substring(idx + 2) }
}

const parts1 = computed(() => {
  if (!dailyChallenge.value) return { before: '', after: '' }
  return splitTemplate(dailyChallenge.value.sentence_template)
})

const parts2 = computed(() => {
  if (!dailyChallenge.value?.sentence_template_2) return { before: '', after: '' }
  return splitTemplate(dailyChallenge.value.sentence_template_2)
})

const detailParts1 = computed(() => {
  if (!detailChallenge.value) return { before: '', after: '' }
  return splitTemplate(detailChallenge.value.sentence_template)
})

const detailParts2 = computed(() => {
  if (!detailChallenge.value?.sentence_template_2) return { before: '', after: '' }
  return splitTemplate(detailChallenge.value.sentence_template_2)
})

const blankPlaceholder = computed(() => {
  if (!dailyChallenge.value) return ''
  return '_'.repeat(dailyChallenge.value.blank_count)
})

const canSubmitDaily = computed(() => {
  if (!dailyChallenge.value || !answer1.value) return false
  if (dailyChallenge.value.sentence_template_2 && !answer2.value) return false
  return true
})

const canSubmitDetail = computed(() => {
  if (!detailChallenge.value) return false
  if (detailChallenge.value.challenge_type === 'fill_blank') {
    if (!detailAnswer1.value) return false
    if (detailChallenge.value.sentence_template_2 && !detailAnswer2.value) return false
  } else {
    if (!detailContinueText.value) return false
  }
  return true
})

const canCreate = computed(() => {
  if (createForm.type === 'continue_line') {
    return createForm.template.trim().length >= 2
  }
  return createForm.template.trim().length >= 2 && createForm.template2.trim().length >= 2
})

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

const formatTime = (dateStr: string) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const dailyHintLevel = ref(0)
const dailyHintText = ref('')
const dailyHintLoading = ref(false)
const dailyHintNextAvailable = ref(true)
const dailyReviewLoading = ref(false)
const dailyReviewData = ref<ChallengeAIReviewResponse | null>(null)

const detailHintLevel = ref(0)
const detailHintText = ref('')
const detailHintLoading = ref(false)
const detailHintNextAvailable = ref(true)
const detailReviewLoading = ref(false)
const detailReviewData = ref<ChallengeAIReviewResponse | null>(null)

const scoreGrade = (score: number) => {
  if (score >= 80) return 'grade-s'
  if (score >= 60) return 'grade-a'
  if (score >= 40) return 'grade-b'
  return 'grade-c'
}

const previewTemplate = (tmpl: string) => {
  return tmpl.replace(/__/g, '(?)')
}

const handleDeleteDetailChallenge = async () => {
  if (!detailChallenge.value) return
  const cid = detailChallenge.value.id
  const ctype = detailChallenge.value.challenge_type
  try {
    await ElMessageBox.confirm(
      '删除题目后，所有相关落笔记录将一并清除，此操作不可撤销。',
      '确认删除题目',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '再想想',
        type: 'warning',
        customClass: 'miaobi-confirm-dialog',
        closeOnClickModal: true,
        distinguishCancelAndClose: true
      }
    )
  } catch {
    return
  }
  try {
    await challengeApi.deleteChallenge(cid)
    closeDetail()
    if (ctype === 'fill_blank') {
      plazaList.value = plazaList.value.filter(c => c.id !== cid)
    } else {
      continueList.value = continueList.value.filter(c => c.id !== cid)
    }
    ElMessage.success('题目已删除')
    await syncUserGrowth()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const handleDeleteChallenge = async (challengeId: number, source: 'plaza' | 'continue') => {
  try {
    await ElMessageBox.confirm(
      '删除题目后，所有相关落笔记录将一并清除，此操作不可撤销。',
      '确认删除题目',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '再想想',
        type: 'warning',
        customClass: 'miaobi-confirm-dialog',
        closeOnClickModal: true,
        distinguishCancelAndClose: true
      }
    )
  } catch {
    return
  }
  try {
    await challengeApi.deleteChallenge(challengeId)
    if (source === 'plaza') {
      plazaList.value = plazaList.value.filter(c => c.id !== challengeId)
    } else {
      continueList.value = continueList.value.filter(c => c.id !== challengeId)
    }
    ElMessage.success('题目已删除')
    await syncUserGrowth()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const handleDeleteResponse = async (submissionId: number) => {
  try {
    await ElMessageBox.confirm(
      '删除此条落笔后，对应经验与积分将一并扣回，此操作不可撤销。',
      '确认删除落笔',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '再想想',
        type: 'warning',
        customClass: 'miaobi-confirm-dialog',
        closeOnClickModal: true,
        distinguishCancelAndClose: true
      }
    )
  } catch {
    return
  }
  try {
    await challengeApi.deleteSubmission(submissionId)
    detailResponses.value = detailResponses.value.filter(r => r.id !== submissionId)
    if (detailChallenge.value) {
      detailChallenge.value.response_count = Math.max(0, detailChallenge.value.response_count - 1)
    }
    ElMessage.success('已删除，经验与积分已扣回')
    await syncUserGrowth()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const syncUserGrowth = async () => {
  if (!userStore.isLogin) return
  await userStore.fetchUserInfo()
}

const loadDaily = async () => {
  try {
    dailyChallenge.value = await challengeApi.getDaily()
    if (dailyChallenge.value) {
      loadDailyResponses()
    }
  } catch {
    dailyChallenge.value = null
  }
}

const loadDailyResponses = async () => {
  if (!dailyChallenge.value) return
  try {
    const data = await challengeApi.getResponses(dailyChallenge.value.id, { page: 1, page_size: 20 })
    dailyResponses.value = data.items
  } catch { /* ignore */ }
}

const loadPlaza = async () => {
  try {
    const data = await challengeApi.getList({ challenge_type: 'fill_blank', page: 1, page_size: 20 })
    plazaList.value = data.items
  } catch { /* ignore */ }
}

const loadContinue = async () => {
  try {
    const data = await challengeApi.getList({ challenge_type: 'continue_line', page: 1, page_size: 20 })
    continueList.value = data.items
  } catch { /* ignore */ }
}

const loadStreak = async () => {
  if (!userStore.isLogin) return
  try {
    const data = await challengeApi.getHistory({ page: 1, page_size: 1 })
    streakDays.value = data.streak_days
  } catch { /* ignore */ }
}

const switchTab = (tab: TabKey) => {
  activeTab.value = tab
  if (tab === 'plaza' && !plazaList.value.length) loadPlaza()
  if (tab === 'continue' && !continueList.value.length) loadContinue()
}

const goProfile = () => {
  router.push('/profile/folio?tab=challenges')
}

const goChallengeCreate = () => {
  switchTab(activeTab.value === 'create' ? 'plaza' : 'create')
}

const handlePrimaryAction = async () => {
  if (activeTab.value === 'daily') {
    if (!dailySubmitted.value) {
      if (canSubmitDaily.value) {
        await submitDaily()
      } else {
        ElMessage.warning('先补全题面，再来落笔')
      }
      return
    }
    switchTab('plaza')
    return
  }
  if (activeTab.value === 'plaza') {
    await loadPlaza()
    return
  }
  if (activeTab.value === 'continue') {
    await loadContinue()
    return
  }
  await handleCreate()
}

const requestDailyHint = async () => {
  if (!dailyChallenge.value || dailyHintLoading.value) return
  if (!userStore.isLogin) { ElMessage.warning('请先登录'); return }
  dailyHintLoading.value = true
  startPhaseLoop(dailyHintStep, hintStages, dailyHintTimer, 2000)
  try {
    const nextLevel = dailyHintLevel.value + 1
    const data = await challengeApi.aiHint(dailyChallenge.value.id, { hint_level: nextLevel })
    dailyHintText.value = data.hint_text
    dailyHintLevel.value = data.hint_level
    dailyHintNextAvailable.value = data.next_available
  } catch {
    ElMessage.warning('AI 提示暂时不可用')
  } finally {
    clearPhaseTimer(dailyHintTimer)
    dailyHintStep.value = 0
    dailyHintLoading.value = false
  }
}

const requestDetailHint = async () => {
  if (!detailChallenge.value || detailHintLoading.value) return
  if (!userStore.isLogin) { ElMessage.warning('请先登录'); return }
  detailHintLoading.value = true
  startPhaseLoop(detailHintStep, hintStages, detailHintTimer, 2000)
  try {
    const nextLevel = detailHintLevel.value + 1
    const data = await challengeApi.aiHint(detailChallenge.value.id, { hint_level: nextLevel })
    detailHintText.value = data.hint_text
    detailHintLevel.value = data.hint_level
    detailHintNextAvailable.value = data.next_available
  } catch {
    ElMessage.warning('AI 提示暂时不可用')
  } finally {
    clearPhaseTimer(detailHintTimer)
    detailHintStep.value = 0
    detailHintLoading.value = false
  }
}

const requestDailyReview = async () => {
  if (!dailyChallenge.value || dailyReviewLoading.value) return
  if (!userStore.isLogin) { ElMessage.warning('请先登录'); return }
  dailyReviewLoading.value = true
  startPhaseLoop(dailyReviewStep, reviewStages, dailyReviewTimer, 2400)
  try {
    dailyReviewData.value = await challengeApi.aiReview(dailyChallenge.value.id)
  } catch {
    ElMessage.warning('AI 赏析暂时不可用')
  } finally {
    clearPhaseTimer(dailyReviewTimer)
    dailyReviewStep.value = 0
    dailyReviewLoading.value = false
  }
}

const requestDetailReview = async () => {
  if (!detailChallenge.value || detailReviewLoading.value) return
  if (!userStore.isLogin) { ElMessage.warning('请先登录'); return }
  detailReviewLoading.value = true
  startPhaseLoop(detailReviewStep, reviewStages, detailReviewTimer, 2400)
  try {
    detailReviewData.value = await challengeApi.aiReview(detailChallenge.value.id)
  } catch {
    ElMessage.warning('AI 赏析暂时不可用')
  } finally {
    clearPhaseTimer(detailReviewTimer)
    detailReviewStep.value = 0
    detailReviewLoading.value = false
  }
}

const openDetail = async (challenge: DailyChallenge) => {
  detailChallenge.value = challenge
  detailAnswer1.value = ''
  detailAnswer2.value = ''
  detailContinueText.value = ''
  detailSubmitted.value = false
  detailResult.value = null
  detailHintLevel.value = 0
  detailHintText.value = ''
  detailHintNextAvailable.value = true
  detailReviewData.value = null
  try {
    const data = await challengeApi.getResponses(challenge.id, { page: 1, page_size: 30 })
    detailResponses.value = data.items
  } catch {
    detailResponses.value = []
  }
}

const closeDetail = () => {
  detailChallenge.value = null
}

const submitDaily = async () => {
  if (!canSubmitDaily.value || !dailyChallenge.value || dailySubmitting.value) return
  dailySubmitting.value = true
  try {
    dailyResult.value = await challengeApi.submit({
      challenge_id: dailyChallenge.value.id,
      answer: answer1.value,
      answer_2: dailyChallenge.value.sentence_template_2 ? answer2.value : undefined,
    })
    dailySubmitted.value = true
    ElMessage.success('落笔成诗！')
    loadDailyResponses()
    loadStreak()
    await syncUserGrowth()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    dailySubmitting.value = false
  }
}

const submitDetail = async () => {
  if (!canSubmitDetail.value || !detailChallenge.value || detailSubmitting.value) return
  detailSubmitting.value = true
  const isBlank = detailChallenge.value.challenge_type === 'fill_blank'
  try {
    detailResult.value = await challengeApi.submit({
      challenge_id: detailChallenge.value.id,
      answer: isBlank ? detailAnswer1.value : detailContinueText.value,
      answer_2: isBlank && detailChallenge.value.sentence_template_2 ? detailAnswer2.value : undefined,
      content: !isBlank ? detailContinueText.value : undefined,
    })
    detailSubmitted.value = true
    ElMessage.success('落笔成诗！')
    const data = await challengeApi.getResponses(detailChallenge.value.id, { page: 1, page_size: 30 })
    detailResponses.value = data.items
    await syncUserGrowth()
    loadStreak()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    detailSubmitting.value = false
  }
}

const handleCreate = async () => {
  if (!canCreate.value) return
  if (!userStore.isLogin) {
    ElMessage.warning('请先登录')
    return
  }
  
  const match = createForm.template.match(/_{2,}/)
  const blankCount = match ? match[0].length : 2
  try {
    await challengeApi.create({
      challenge_type: createForm.type,
      sentence_template: createForm.template,
      sentence_template_2: createForm.type === 'fill_blank' && createForm.template2 ? createForm.template2 : undefined,
      blank_count: createForm.type === 'fill_blank' ? blankCount : 1,
      hint: createForm.hint || undefined,
    })
    ElMessage.success('出题成功！')
    createForm.template = ''
    createForm.template2 = ''
    createForm.hint = ''
    aiCheckResult.value = null
    if (createForm.type === 'fill_blank') {
      loadPlaza()
    } else {
      loadContinue()
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '出题失败')
  }
}

const handleAICheck = async () => {
  if (!createForm.template || !createForm.template2 || aiGenerating.value) return
  if (!userStore.isLogin) {
    ElMessage.warning('请先登录')
    return
  }
  aiGenerating.value = true
  aiCheckResult.value = null
  aiCurrentStep.value = 0
  
  clearPhaseTimer(createProgressTimer)
  createProgressTimer.value = window.setInterval(() => {
    if (aiCurrentStep.value < aiProgressSteps.value.length - 1) {
      aiCurrentStep.value++
    }
  }, 5000)
  
  try {
    const res = await challengeApi.aiCheckChallenge({
      sentence_template: createForm.template,
      sentence_template_2: createForm.template2 || undefined,
      user_answer: createForm.hint || undefined,
    })
    aiCheckResult.value = res
    if (res.is_valid) {
      ElMessage.success('翰林赞许')
    } else {
      ElMessage.warning('翰林批注：请查看建议')
    }
  } catch {
    ElMessage.warning('翰林暂时不在')
  } finally {
    clearPhaseTimer(createProgressTimer)
    aiGenerating.value = false
    aiCurrentStep.value = 0
  }
}

onMounted(async () => {
  loading.value = true
  await syncUserGrowth()
  await loadDaily()
  loadStreak()
  loading.value = false

  const cid = route.query.challenge_id
  if (cid) {
    try {
      const c = await challengeApi.getDetail(Number(cid))
      if (c) {
        switchTab('plaza')
        openDetail(c)
      }
    } catch { /* ignore */ }
  }
})
</script>

<style scoped src="./styles/index.css"></style>
