<template>
  <div
    id="node-preview-popover"
    class="node-preview"
    :style="nodePreviewStyle"
    :hidden="!nodePreview.visible"
  >
    <article v-if="nodePreview.node" class="graph-node preview-node">
      <div class="node-header">
        <span class="node-type">preview / {{ nodePreview.node.className }}</span>
        <h3>{{ nodePreview.node.title }}</h3>
      </div>
      <div class="node-body">
        <p>{{ nodePreview.node.description }}</p>
        <div class="ports">
          <div class="port-column">
            <span class="port-title">Inputs</span>
            <PortList :node="previewNode" direction="input" :connection-drag="null" />
          </div>
          <div class="port-column">
            <span class="port-title">Outputs</span>
            <PortList :node="previewNode" direction="output" :connection-drag="null" />
          </div>
        </div>
        <form v-if="previewNode && Object.keys(previewNode.props).length > 0" class="node-properties" autocomplete="off" @submit.prevent>
          <div v-for="(value, key) in previewNode.props" :key="key" class="field">
            <label>{{ key }}</label>
            <input :value="value" readonly>
          </div>
        </form>
      </div>
    </article>
  </div>
</template>

<script>
import PortList from "./PortList.vue";

export default {
  name: "NodePreview",
  components: {PortList},
  props: {
    nodePreview: {type: Object, required: true},
    nodePreviewStyle: {type: Object, required: true},
    previewNode: {type: Object, default: null},
  },
};
</script>
