<template>
  <section class="node-group" :data-depth="String(depth)">
    <h4>{{ item.title }}</h4>
    <template v-for="child in item.items" :key="child.id || child.type">
      <CatalogGroup
        v-if="child.kind === 'group'"
        :item="child"
        :depth="depth + 1"
        @preview="(...args) => $emit('preview', ...args)"
        @move-preview="$emit('move-preview', $event)"
        @hide-preview="$emit('hide-preview')"
      />
      <NodeCard
        v-else-if="child.kind === 'node'"
        :node="child"
        @preview="(...args) => $emit('preview', ...args)"
        @move-preview="$emit('move-preview', $event)"
        @hide-preview="$emit('hide-preview')"
      />
    </template>
  </section>
</template>

<script>
import NodeCard from "./NodeCard.vue";

export default {
  name: "CatalogGroup",
  components: {NodeCard},
  props: {
    item: {type: Object, required: true},
    depth: {type: Number, default: 0},
  },
  emits: ["preview", "move-preview", "hide-preview"],
};
</script>
