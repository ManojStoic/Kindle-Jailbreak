-- Fetch a bounded snapshot over TLS, trusting only this dashboard certificate.
local M = {}
local dir = "/mnt/us/kindlelab/lan/"
local output = "/mnt/us/kindlelab/dashboard-snapshot.txt"

local function read_line(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local value = f:read("*l")
    f:close()
    return value
end

function M.fetch()
    local host = read_line(dir .. "host.txt")
    local token = read_line(dir .. "token.txt")
    if not host or not host:match("^%d+%.%d+%.%d+%.%d+$") or not token
        or not token:match("^[A-Za-z0-9_-]+$") then return false end
    local ok, https = pcall(require, "ssl.https")
    if not ok then return false end
    https.TIMEOUT = 4
    local chunks, size = {}, 0
    local function sink(chunk)
        if chunk then
            size = size + #chunk
            if size > 2048 then return nil, "response too large" end
            chunks[#chunks + 1] = chunk
        end
        return 1
    end
    local request_ok, res, code = pcall(https.request, {
        url = "https://" .. host .. ":8766/snapshot",
        method = "GET", redirect = false,
        headers = { authorization = "Bearer " .. token },
        verify = "peer", cafile = dir .. "server-cert.pem", sink = sink,
    })
    if not request_ok or not res or tonumber(code) ~= 200 then return false end
    local body = table.concat(chunks)
    if not body:match("^Weather: [^\n]*\nEvent: [^\n]*\nUpdated: [^\n]*\n$") then
        return false
    end
    local temp = output .. ".pending"
    local f = io.open(temp, "w")
    if not f then return false end
    local written = f:write(body)
    local closed = f:close()
    if not written or not closed then os.remove(temp); return false end
    local renamed = os.rename(temp, output)
    if not renamed then os.remove(temp); return false end
    return true
end

return M
