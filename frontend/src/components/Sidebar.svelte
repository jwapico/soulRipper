<script lang="ts">
    let { children, style = "" } = $props()
</script>

<div style="display: flex; flex-direction: column; {style}">
    Sidebar

    {@render children()}
</div>