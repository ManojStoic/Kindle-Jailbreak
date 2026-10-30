local Device = require("device")
local Font = require("ui/font")
local TextBoxWidget = require("ui/widget/textboxwidget")
local UIManager = require("ui/uimanager")

local Screen = Device.screen
local M = {
    id = "kindlelab_dashboard",
    name = "KindleLab Dashboard",
    category = "extras",
    enabled_key = "kindlelab_dashboard_enabled",
    default_on = false,
}

local function greeting()
    local f = io.open("/mnt/us/kindlelab/dashboard-greeting.txt", "r")
    if not f then return "Welcome!" end
    local text = f:read("*l")
    f:close()
    if not text or text == "" then return "Welcome!" end
    return text:sub(1, 80)
end

local function wifi_name()
    local ok, network = pcall(require, "ui/network/manager")
    if not ok or not network then return "Unavailable" end
    local connected, is_connected = pcall(network.isConnected, network)
    if not connected or not is_connected then return "Not connected" end
    local found, current = pcall(network.getCurrentNetwork, network)
    if not found or not current or not current.ssid or current.ssid == "" then
        return "Connected (name unavailable)"
    end
    -- Never send the network name to the laptop or write it to our own logs.
    return tostring(current.ssid):gsub("[%c]", " "):sub(1, 48)
end

local function snapshot_text()
    local f = io.open("/mnt/us/kindlelab/dashboard-snapshot.txt", "r")
    if not f then return "Weather and events: not connected" end
    local lines = {}
    for _ = 1, 3 do
        local line = f:read("*l")
        if not line then break end
        lines[#lines + 1] = line
    end
    f:close()
    return table.concat(lines, "\n")
end

function M.getHeight(_ctx)
    return Screen:scaleBySize(220)
end

local function clock_stamp()
    -- Uses the device's configured local timezone, including DST if supported.
    local t = os.date("*t", os.time())
    return t and string.format("%02d:%02d  %02d-%02d-%04d", t.hour, t.min, t.day, t.month, t.year) or "Unavailable"
end

function M.build(w, ctx)
    local widget = TextBoxWidget:new{
        text = greeting() .. "\nLocal time: " .. clock_stamp() .. "\nWi-Fi: " .. wifi_name()
            .. "\n" .. snapshot_text(),
        width = w,
        face = Font:getFace("cfont", 16),
    }
    if ctx and ctx._screen_widget then ctx._screen_widget._kindlelab_clock_widget = widget end
    return widget
end

function M.refreshClock(screen)
    local widget = screen and screen._kindlelab_clock_widget
    if not widget or not widget.text then return false end
    local updated, count = widget.text:gsub("\nLocal time: [^\n]*", "\nLocal time: " .. clock_stamp(), 1)
    if count ~= 1 or updated == widget.text then return count == 1 end
    local old = widget:getSize()
    widget:setText(updated)
    local new = widget:getSize()
    if old.w ~= new.w or old.h ~= new.h then return false end
    UIManager:setDirty(screen, function() return "ui", widget.dimen end)
    return true
end

return M
