import type { Viewport } from 'pixi-viewport'
import type { GraphRenderNode, GraphScene, LabelOverlayState } from './types'

interface ManagedLabel {
  element: HTMLDivElement
  title: HTMLSpanElement
  subtitle: HTMLSpanElement
  key: string
  width: number
  height: number
}

interface ScreenPoint {
  x: number
  y: number
}

export class LabelOverlay {
  private readonly host: HTMLElement
  private readonly nodeLabels = new Map<string, ManagedLabel>()
  private readonly edgeChip: HTMLDivElement

  constructor(host: HTMLElement) {
    this.host = host
    this.host.innerHTML = ''

    this.edgeChip = document.createElement('div')
    this.edgeChip.className = 'graph-edge-chip'
    this.edgeChip.style.display = 'none'
    this.host.appendChild(this.edgeChip)
  }

  update(
    scene: GraphScene,
    viewport: Viewport,
    nodePositions: Map<string, ScreenPoint>,
    state: LabelOverlayState,
  ) {
    const hostRect = this.host.getBoundingClientRect()
    const visibleIds = new Set<string>()
    const boxes: Array<{ left: number; top: number; right: number; bottom: number }> = []
    const zoomScale = viewport.scale.x
    const maxVisibleLabels = resolveVisibleLabelLimit(scene, zoomScale)

    const candidates = scene.nodes
      .map((node) => {
        const world = nodePositions.get(node.id)
        if (!world) return null
        const screen = viewport.toScreen(world)
        const priority = getLabelPriority(node, state, zoomScale)

        return {
          node,
          priority,
          screen: { x: screen.x, y: screen.y },
          scale: viewport.scale.x,
        }
      })
      .filter((candidate): candidate is NonNullable<typeof candidate> => candidate !== null)
      .filter((candidate) => candidate.priority > 0)
      .filter((candidate) => isWithinViewport(candidate.screen, hostRect.width, hostRect.height))
      .sort((left, right) => right.priority - left.priority)

    for (const candidate of candidates) {
      if (visibleIds.size >= maxVisibleLabels) break

      const label = this.ensureLabel(candidate.node)
      const positions = resolveLabelPositions(
        candidate.node,
        candidate.screen,
        candidate.scale,
        label,
        hostRect.width,
        hostRect.height,
      )
      let chosenPosition: ScreenPoint | null = null
      let chosenBounds: { left: number; top: number; right: number; bottom: number } | null = null

      for (const position of positions) {
        const displayBounds = {
          left: position.x,
          top: position.y,
          right: position.x + label.width,
          bottom: position.y + label.height,
        }
        const bounds = resolveCollisionBounds(candidate.node, displayBounds)

        if (!withinBounds(displayBounds, hostRect.width, hostRect.height)) continue
        if (boxes.some((box) => intersects(box, bounds))) continue

        chosenPosition = position
        chosenBounds = bounds
        break
      }

      if (!chosenPosition || !chosenBounds) continue

      label.element.className = buildLabelClass(candidate.node, state)
      label.element.style.display = 'flex'
      label.element.style.transform = `translate(${chosenPosition.x}px, ${chosenPosition.y}px)`

      visibleIds.add(candidate.node.id)
      boxes.push(chosenBounds)
    }

    this.nodeLabels.forEach((label, id) => {
      if (!visibleIds.has(id)) {
        label.element.style.display = 'none'
      }
    })

    const hoveredAnchor = state.edgeAnchors.find((anchor) => anchor.id === state.hoveredEdgeId)
    if (!hoveredAnchor?.label) {
      this.edgeChip.style.display = 'none'
      return
    }

    const chipPoint = viewport.toScreen({ x: hoveredAnchor.x, y: hoveredAnchor.y })
    this.edgeChip.textContent = hoveredAnchor.label
    this.edgeChip.style.display = 'block'
    const chipWidth = this.edgeChip.offsetWidth
    const chipHeight = this.edgeChip.offsetHeight
    this.edgeChip.style.transform = `translate(${chipPoint.x - chipWidth / 2}px, ${chipPoint.y - chipHeight - 18}px)`
  }

  destroy() {
    this.nodeLabels.clear()
    this.host.innerHTML = ''
  }

  private ensureLabel(node: GraphRenderNode) {
    const existing = this.nodeLabels.get(node.id)
    const textKey = `${node.name}|${node.subtitle ?? ''}|${node.tier}`

    if (existing) {
      if (existing.key !== textKey) {
        existing.title.textContent = node.name
        existing.subtitle.textContent = node.subtitle ?? ''
        existing.subtitle.style.display = node.subtitle ? 'block' : 'none'
        existing.key = textKey
        existing.width = existing.element.offsetWidth
        existing.height = existing.element.offsetHeight
      }
      return existing
    }

    const element = document.createElement('div')
    element.className = buildLabelClass(node, {
      hoveredNodeId: null,
      hoveredEdgeId: null,
      selectedNodeId: null,
      edgeAnchors: [],
    })
    element.style.display = 'flex'
    element.style.visibility = 'hidden'

    const title = document.createElement('span')
    title.className = 'graph-node-label__title'
    title.textContent = node.name

    const subtitle = document.createElement('span')
    subtitle.className = 'graph-node-label__subtitle'
    subtitle.textContent = node.subtitle ?? ''
    subtitle.style.display = node.subtitle ? 'block' : 'none'

    element.append(title, subtitle)
    this.host.appendChild(element)

    const label = {
      element,
      title,
      subtitle,
      key: textKey,
      width: element.offsetWidth,
      height: element.offsetHeight,
    } satisfies ManagedLabel

    element.style.display = 'none'
    element.style.visibility = ''

    this.nodeLabels.set(node.id, label)
    return label
  }
}

function getLabelPriority(node: GraphRenderNode, state: LabelOverlayState, zoomScale: number) {
  if (state.selectedNodeId === node.id) return node.labelPriority + 200
  if (state.hoveredNodeId === node.id) return node.labelPriority + 160
  if (node.type === 'dynasty' && node.tier !== 'core' && !node.labelVisible && zoomScale < 1.12) return -1
  if (node.tier === 'minor') {
    if (node.type !== 'poet') return -1
    if (zoomScale < 0.42 && !node.labelVisible) return -1
    if (zoomScale < 0.5 && !node.labelVisible && node.importance < 0.62) return -1
    const zoomBoost = zoomScale >= 1.7
      ? 72
      : zoomScale >= 1.28
        ? 48
        : zoomScale >= 0.92
          ? 28
          : zoomScale >= 0.76
            ? 18
          : zoomScale >= 0.68
            ? 14
            : 0
    const labelBoost = node.labelVisible ? 26 : 0
    const prominenceBoost = node.importance >= 0.78 ? 20 : node.importance >= 0.68 ? 12 : node.importance >= 0.58 ? 6 : 0
    return node.labelPriority + 12 + labelBoost + zoomBoost + prominenceBoost + Math.round(node.importance * 24)
  }
  if (node.tier === 'core') return node.labelPriority + 120
  if (node.labelVisible) return node.labelPriority + 32 + Math.round((zoomScale - 0.36) * 24)
  return -1
}

function buildLabelClass(node: GraphRenderNode, state: LabelOverlayState) {
  const classes = ['graph-node-label', `tier-${node.tier}`]

  if (state.selectedNodeId === node.id) classes.push('is-selected')
  if (state.hoveredNodeId === node.id) classes.push('is-hovered')
  if (node.type === 'dynasty') classes.push('type-dynasty')
  if (node.type === 'category') classes.push('type-category')

  return classes.join(' ')
}

function resolveLabelPositions(
  node: GraphRenderNode,
  screen: ScreenPoint,
  scale: number,
  label: ManagedLabel,
  hostWidth: number,
  hostHeight: number,
) {
  const primary = resolvePrimaryLabelPosition(node, screen, scale, label, hostWidth, hostHeight)
  if (node.tier === 'core') return [primary]

  const offset = Math.max(node.radius * scale, 12) + (node.tier === 'major' ? 16 : 11)
  const sidePush = offset + (node.tier === 'major' ? 14 : 9)
  const positions = [
    primary,
    { x: screen.x + sidePush, y: screen.y - label.height / 2 - 2 },
    { x: screen.x - label.width - sidePush, y: screen.y - label.height / 2 - 2 },
    { x: screen.x - label.width / 2, y: screen.y - offset - label.height + 2 },
    { x: screen.x - label.width / 2, y: screen.y + offset + 7 },
    { x: screen.x + sidePush * 0.72, y: screen.y - label.height - offset * 0.32 },
    { x: screen.x - label.width - sidePush * 0.72, y: screen.y + offset * 0.18 },
  ]

  return dedupeLabelPositions(positions)
}

function resolvePrimaryLabelPosition(
  node: GraphRenderNode,
  screen: ScreenPoint,
  scale: number,
  label: ManagedLabel,
  hostWidth: number,
  hostHeight: number,
) {
  if (node.tier === 'core') {
    return {
      x: screen.x - label.width / 2,
      y: screen.y - label.height * 1.62 - Math.max(node.radius * scale * 1.18, 34),
    }
  }

  const dx = screen.x - hostWidth / 2
  const dy = screen.y - hostHeight / 2
  const distance = Math.max(Math.hypot(dx, dy), 1)
  const dirX = dx / distance
  const dirY = dy / distance
  const offset = Math.max(node.radius * scale, 12) + (node.tier === 'major' ? 14 : 10)

  if (distance < 150) {
    if (Math.abs(dx) > Math.abs(dy) * 1.12) {
      const push = offset + (node.tier === 'major' ? 12 : 8)
      const placeRight = dx > 0

      return {
        x: placeRight ? screen.x + push : screen.x - label.width - push,
        y: screen.y - label.height / 2 + Math.sign(dy || 1) * 4,
      }
    }

    if (dy > 0) {
      return {
        x: screen.x - label.width / 2 + dirX * 10,
        y: screen.y + offset + 8,
      }
    }

    return {
      x: screen.x - label.width / 2 + Math.sign(dx || 1) * 16,
      y: screen.y - offset - label.height * 0.72,
    }
  }

  const alignRight = dirX > 0.15

  return {
    x: screen.x + dirX * offset - (alignRight ? label.width : 0),
    y: screen.y + dirY * offset - label.height / 2,
  }
}

function resolveVisibleLabelLimit(scene: GraphScene, zoomScale: number) {
  const base = scene.maxLabels
  if (scene.level === 2) {
    if (zoomScale >= 2.1) return Math.min(scene.nodes.length, base + 38)
    if (zoomScale >= 1.6) return Math.min(scene.nodes.length, base + 30)
    if (zoomScale >= 1.2) return Math.min(scene.nodes.length, base + 22)
    if (zoomScale >= 0.88) return Math.min(scene.nodes.length, base + 14)
    if (zoomScale >= 0.64) return Math.min(scene.nodes.length, base + 8)
    if (zoomScale >= 0.5) return Math.min(scene.nodes.length, base + 4)
  }

  if (scene.level === 1) {
    if (zoomScale >= 1.4) return Math.min(scene.nodes.length, base + 10)
    if (zoomScale >= 1.05) return Math.min(scene.nodes.length, base + 5)
  }

  return base
}

function isWithinViewport(point: ScreenPoint, width: number, height: number) {
  return point.x >= -60 && point.x <= width + 60 && point.y >= -60 && point.y <= height + 60
}

function withinBounds(
  box: { left: number; top: number; right: number; bottom: number },
  width: number,
  height: number,
) {
  return box.left >= -24 && box.right <= width + 24 && box.top >= -24 && box.bottom <= height + 24
}

function intersects(
  left: { left: number; top: number; right: number; bottom: number },
  right: { left: number; top: number; right: number; bottom: number },
) {
  return !(
    left.right < right.left
    || left.left > right.right
    || left.bottom < right.top
    || left.top > right.bottom
  )
}

function resolveCollisionBounds(
  node: GraphRenderNode,
  bounds: { left: number; top: number; right: number; bottom: number },
) {
  const horizontalInset = node.tier === 'core' ? 1 : node.tier === 'major' ? 6 : 8
  const verticalInset = node.tier === 'core' ? 1 : node.tier === 'major' ? 4 : 5

  return {
    left: bounds.left + horizontalInset,
    top: bounds.top + verticalInset,
    right: bounds.right - horizontalInset,
    bottom: bounds.bottom - verticalInset,
  }
}

function dedupeLabelPositions(positions: ScreenPoint[]) {
  const seen = new Set<string>()

  return positions.filter((position) => {
    const key = `${Math.round(position.x)}:${Math.round(position.y)}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}
