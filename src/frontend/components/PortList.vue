<template>
  <span v-if="ports.length === 0" class="node-type">none</span>
  <button
    v-for="port in ports"
    v-else
    :key="portName(port)"
    type="button"
    class="port"
    :class="[direction, {compatible: connectionDrag && node.id !== connectionDrag.nodeId && direction !== connectionDrag.direction}]"
    :data-node-id="node.id"
    :data-port="portName(port)"
    :data-port-type="portType(port)"
    :data-direction="direction"
    :data-compatible="connectionDrag && node.id !== connectionDrag.nodeId && direction !== connectionDrag.direction ? 'true' : 'false'"
    @pointerdown.stop="$emit('start-connection', $event)"
  ><span>{{ portName(port) }}</span><span class="port-type">{{ portType(port) }}</span></button>
</template>

<script>
import {portName, portType} from "../graph.js";

export default {
  name: "PortList",
  props: {
    node: {type: Object, required: true},
    direction: {type: String, required: true},
    connectionDrag: {type: Object, default: null},
  },
  emits: ["start-connection"],
  methods: {portName, portType},
  computed: {
    ports() {
      return this.direction === "input" ? this.node.inputs : this.node.outputs;
    },
  },
};
</script>
