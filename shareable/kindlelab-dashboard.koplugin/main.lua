local WidgetContainer = require("ui/widget/container/widgetcontainer")
local UIManager = require("ui/uimanager")
local logger = require("logger")
local util = require("ffi/util")

local Dashboard = WidgetContainer:extend{
    name = "kindlelab_dashboard",
    is_doc_only = false,
}

function Dashboard:init()
    -- All plugin roots have been added to package.path by KOReader's loader.
    -- Defer registration until the other plugins have been initialized.
    UIManager:scheduleIn(0, function()
        local ok, registry = pcall(require, "modules/moduleregistry")
        if not ok or not registry then
            logger.warn("KindleLab: SimpleUI module registry unavailable")
            return
        end
        local loaded, module = pcall(require, "kindlelab_module")
        if not loaded then
            logger.warn("KindleLab: dashboard module could not be loaded")
            return
        end
        registry.register(module)
    end)
    self._kindlelab_stopped = false
    self._kindlelab_tick = function() self:kindlelabRefresh() end
    UIManager:scheduleIn(5, self._kindlelab_tick)
    self._kindlelab_clock_tick = function() self:kindlelabClockTick() end
    UIManager:scheduleIn(60 - (os.time() % 60), self._kindlelab_clock_tick)
end

function Dashboard:kindlelabClockTick()
    if self._kindlelab_stopped then return end
    local ok, engine = pcall(require, "screens/sui_homescreen")
    local mod_ok, module = pcall(require, "kindlelab_module")
    if ok and engine and mod_ok and module then
        local screen = engine.getInstance and engine.getInstance("hs")
        if screen and UIManager:getTopmostVisibleWidget() == screen then
            local refreshed, result = pcall(module.refreshClock, screen)
            if (not refreshed or not result) and engine.rebuildLayout then
                pcall(engine.rebuildLayout, { keep_wallpaper = true })
            end
        end
    end
    UIManager:scheduleIn(60 - (os.time() % 60), self._kindlelab_clock_tick)
end

function Dashboard:kindlelabRefresh()
    if self._kindlelab_stopped then return end
    local ok, network = pcall(require, "ui/network/manager")
    local connected, online = false, false
    if ok and network then connected, online = pcall(network.isConnected, network) end
    if connected and online then
        local pid = util.runInSubProcess(function()
            local loaded, sync = pcall(require, "kindlelab_sync")
            local success = false
            if loaded and sync then
                local completed, result = pcall(sync.fetch)
                success = completed and result == true
            end
            local status = io.open("/mnt/us/kindlelab/lan/status.txt", "w")
            if status then
                status:write(success and "connected\n" or "unavailable\n")
                status:close()
            end
        end)
        if pid then
            self._kindlelab_pid = pid
            local function poll()
                if util.isSubProcessDone(pid) then
                    self._kindlelab_pid = nil
                    if not self._kindlelab_stopped then
                        local loaded, screen = pcall(require, "screens/sui_homescreen")
                        if loaded and screen and screen.rebuildLayout then
                            pcall(screen.rebuildLayout, { keep_wallpaper = true })
                        end
                    end
                elseif not self._kindlelab_stopped then
                    UIManager:scheduleIn(1, poll)
                end
            end
            UIManager:scheduleIn(1, poll)
        end
    end
    UIManager:scheduleIn(900, self._kindlelab_tick)
end

function Dashboard:onCloseWidget()
    self._kindlelab_stopped = true
    if self._kindlelab_tick then UIManager:unschedule(self._kindlelab_tick) end
    if self._kindlelab_clock_tick then UIManager:unschedule(self._kindlelab_clock_tick) end
    if self._kindlelab_pid then pcall(util.terminateSubProcess, self._kindlelab_pid) end
end

return Dashboard
