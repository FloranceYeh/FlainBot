<template>
  <article
    class="node-card"
    draggable="true"
    :data-node-type="node.type"
    @dragstart="handleNodeCardDragStart"
    @mouseenter="$emit('preview', node, $event)"
    @mousemove="$emit('move-preview', $event)"
    @mouseleave="$emit('hide-preview')"
  >
    <span class="node-type">{{ node.className }}</span>
    <h4>{{ node.title }}</h4>
    <p>{{ node.description }}</p>
  </article>
</template>

<script>
export default {
  name: "NodeCard",
  props: {node: {type: Object, required: true}},
  emits: ["preview", "move-preview", "hide-preview"],
  methods: {
    handleNodeCardDragStart(event) {
      event.dataTransfer.effectAllowed = "copy";
      event.dataTransfer.setData("application/x-flainbot-node-type", this.node.type);
    },
  },
};
</script>
