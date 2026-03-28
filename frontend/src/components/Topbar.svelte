<script lang="ts">
    let { children, style = "" } = $props()
</script>

<div style="display:flex; {style}">
    <p>Topbar</p>
    {@render children()}
</div>