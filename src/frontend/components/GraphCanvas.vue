<template>
  <section class="canvas-panel" aria-labelledby="graph-title">
    <div class="canvas-toolbar">
      <h2 id="graph-title">FlainBot Node Planner</h2>
      <p id="status-message" class="status-message" :class="statusType" role="status" aria-live="polite">{{ statusMessage }}</p>
      <span id="graph-count" class="count">{{ graph.nodes.length }} nodes / {{ graph.edges.length }} edges</span>
      <div class="canvas-actions">
        <button id="save-graph" type="button" @click="$emit('save-graph')">Save</button>
        <button id="reset-graph" type="button" @click="$emit('reset-graph')">Reset</button>
      </div>
    </div>
    <div
      id="graph-canvas"
      ref="graphCanvas"
      class="graph-canvas"
      @pointermove="$emit('canvas-pointer-move', $event)"
      @pointerup="$emit('canvas-pointer-up', $event)"
      @pointercancel="$emit('canvas-pointer-up', $event)"
      @wheel.prevent="$emit('zoom-canvas', $event)"
      @pointerdown="$emit('canvas-pan', $event)"
      @dragover.prevent
      @drop.prevent="$emit('canvas-drop', $event)"
    >
      <div id="canvas-space" class="canvas-space" data-canvas-space :style="canvasSpaceStyle">
        <svg id="edge-layer" class="edge-layer">
          <path v-for="edge in renderedEdges" :key="edge.key" :d="edge.d"></path>
          <polygon
            v-for="edge in renderedEdges"
            :key="`${edge.key}:arrow`"
            class="edge-arrow"
            points="-6 -4, 6 0, -6 4"
            :transform="`translate(${edge.arrow.x} ${edge.arrow.y}) rotate(${edge.arrow.angle})`"
          ></polygon>
          <path v-if="previewConnectionPath" class="preview-connection" :d="previewConnectionPath"></path>
        </svg>
        <div id="node-layer" class="node-layer">
          <article
            v-for="node in graph.nodes"
            :key="node.id"
            class="graph-node"
            :class="{selected: node.id === selectedId}"
            :style="{left: `${node.x}px`, top: `${node.y}px`}"
            :data-node-id="node.id"
            @pointerdown="$emit('select-node', node.id)"
          >
            <button
              type="button"
              class="node-remove-dot"
              title="Remove node"
              :aria-label="`Remove ${node.id}`"
              @pointerdown.stop
              @click.stop="$emit('remove-node', node.id)"
            ></button>
            <div class="node-header" data-drag-handle="true" @pointerdown.stop="$emit('start-drag', $event, node.id)">
              <span class="node-type">{{ node.id }} / {{ node.className }}</span>
              <h3>{{ node.title }}</h3>
            </div>
            <div class="node-body">
              <div class="ports">
                <div class="port-column">
                  <span class="port-title">Inputs</span>
                  <PortList :node="node" direction="input" :connection-drag="connectionDrag" @start-connection="$emit('start-connection', $event)" />
                </div>
                <div class="port-column">
                  <span class="port-title">Outputs</span>
                  <PortList :node="node" direction="output" :connection-drag="connectionDrag" @start-connection="$emit('start-connection', $event)" />
                </div>
              </div>
              <form v-if="Object.keys(node.props).length > 0 || node.type === 'provider_call' || node.type === 'persona'" class="node-properties" autocomplete="off" @submit.prevent>
                <div v-if="node.type === 'provider_call'" class="field">
                  <label>provider_id</label>
                  <select :value="node.props.provider_id" data-prop-key="provider_id" @input="$emit('update-property', node.id, 'provider_id', $event.target.value)">
                    <option value="">Select provider</option>
                    <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.id }} / {{ provider.format }}</option>
                  </select>
                </div>
                <div v-else-if="node.type === 'persona'" class="field">
                  <label>persona_id</label>
                  <select :value="node.props.persona_id" data-prop-key="persona_id" @input="$emit('update-property', node.id, 'persona_id', $event.target.value)">
                    <option value="">Select persona</option>
                    <option v-for="persona in personas" :key="persona.persona_id" :value="persona.persona_id">{{ persona.persona_id }}</option>
                  </select>
                </div>
                <template v-else>
                  <div v-for="(value, key) in node.props" :key="key" class="field">
                    <label>{{ key }}</label>
                    <input :value="value" :data-prop-key="key" @input="$emit('update-property', node.id, key, $event.target.value)">
                  </div>
                </template>
              </form>
              <pre v-if="node.type === 'display_data'" class="display-node-result">{{ nodeDisplayText(node) }}</pre>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import PortList from "./PortList.vue";

export default {
  name: "GraphCanvas",
  components: {PortList},
  props: {
    canvasSpaceStyle: {type: Object, required: true},
    connectionDrag: {type: Object, default: null},
    graph: {type: Object, required: true},
    nodeDisplayText: {type: Function, required: true},
    personas: {type: Array, required: true},
    previewConnectionPath: {type: String, required: true},
    providers: {type: Array, required: true},
    renderedEdges: {type: Array, required: true},
    selectedId: {type: String, default: null},
    statusMessage: {type: String, required: true},
    statusType: {type: String, required: true},
  },
  mounted() {
    this.$emit("canvas-ref", this.$refs.graphCanvas);
  },
  emits: [
    "canvas-drop",
    "canvas-pan",
    "canvas-pointer-move",
    "canvas-pointer-up",
    "canvas-ref",
    "remove-node",
    "reset-graph",
    "save-graph",
    "select-node",
    "start-connection",
    "start-drag",
    "update-property",
    "zoom-canvas",
  ],
};
</script>
