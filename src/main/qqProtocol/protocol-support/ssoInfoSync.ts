import { AppInfo, DeviceInfo } from './appInfo'
import { getActiveProfile } from './profiles'

// --- Protobuf encoding helpers ---

function encodeVarint(value: number | bigint): Buffer {
  const bytes: number[] = []
  let v = typeof value === 'bigint' ? value : BigInt(value)
  if (v === 0n) {
    bytes.push(0)
  } else {
    while (v > 0n) {
      const b = Number(v & 0x7fn)
      v >>= 7n
      bytes.push(v > 0n ? b | 0x80 : b)
    }
  }
  return Buffer.from(bytes)
}

function protoTag(field: number, wireType: number): Buffer {
  return encodeVarint((field << 3) | wireType)
}

function protoVarintField(field: number, value: number | bigint): Buffer {
  return Buffer.concat([protoTag(field, 0), encodeVarint(value)])
}

function protoStringField(field: number, value: string): Buffer {
  const data = Buffer.from(value, 'utf-8')
  return Buffer.concat([protoTag(field, 2), encodeVarint(data.length), data])
}

function protoBytesField(field: number, data: Buffer): Buffer {
  return Buffer.concat([protoTag(field, 2), encodeVarint(data.length), data])
}

function protoMessageField(field: number, content: Buffer): Buffer {
  return protoBytesField(field, content)
}

// --- SsoInfoSync (Register) ---

function buildRegisterDeviceInfo(): Buffer {
  const parts: Buffer[] = []
  parts.push(protoStringField(1, DeviceInfo.devName))
  parts.push(protoStringField(2, AppInfo.kernel))
  parts.push(protoStringField(3, getActiveProfile().systemKernel))
  parts.push(protoStringField(4, ''))
  parts.push(protoStringField(5, AppInfo.vendorOs))
  return Buffer.concat(parts)
}

function buildRegisterInfo(guid: Buffer, isFirstOnline: boolean = true): Buffer {
  const parts: Buffer[] = []
  parts.push(protoStringField(1, guid.toString('hex')))
  parts.push(protoVarintField(2, 0))
  parts.push(protoStringField(3, AppInfo.currentVersion))
  parts.push(protoVarintField(4, isFirstOnline ? 1 : 0))
  parts.push(protoVarintField(5, 2052))
  parts.push(protoMessageField(6, buildRegisterDeviceInfo()))
  parts.push(protoVarintField(7, 0))
  // f8/f9/f10 match real QQ 3.2.28 capture (was 6/0/{1,1}, diverged; aligned 2026-10-05)
  parts.push(protoVarintField(8, 0))
  parts.push(protoVarintField(9, 1))
  const bizInfo = Buffer.concat([
    protoVarintField(1, 0),
    protoVarintField(2, 0),
  ])
  parts.push(protoMessageField(10, bizInfo))
  parts.push(protoVarintField(11, 0))
  parts.push(protoVarintField(12, 1))
  return Buffer.concat(parts)
}

// c2c/group sync cookies are empty on real QQ 3.2.28 (old impl wrote {1:0})
function buildC2cMsgCookie(): Buffer {
  return Buffer.alloc(0)
}

export function buildSsoInfoSync(guid: Buffer, isFirstOnline: boolean = true): Buffer {
  const parts: Buffer[] = []
  // f1 = 1759 on real QQ 3.2.28 (was 735, diverged; aligned 2026-10-05)
  parts.push(protoVarintField(1, 1759))
  parts.push(protoVarintField(2, Math.floor(Math.random() * 0xFFFFFFFF)))
  parts.push(protoVarintField(4, 2))
  parts.push(protoVarintField(5, 0n))

  const c2cSync = Buffer.concat([
    protoMessageField(1, buildC2cMsgCookie()),
    protoVarintField(2, 0n),
    protoMessageField(3, buildC2cMsgCookie()),
  ])
  parts.push(protoMessageField(6, c2cSync))

  // real QQ 3.2.28 sends an empty top-level f8 (Bot omitted it)
  parts.push(protoMessageField(8, Buffer.alloc(0)))

  parts.push(protoMessageField(9, buildRegisterInfo(guid, isFirstOnline)))

  // real QQ 3.2.28: f10 = { f2:0, f4:{ f1:0 } } (old {1:0,2:2} had wrong shape)
  const f10 = Buffer.concat([
    protoVarintField(2, 0),
    protoMessageField(4, protoVarintField(1, 0)),
  ])
  parts.push(protoMessageField(10, f10))

  const appState = Buffer.concat([
    protoVarintField(1, 0),
    protoVarintField(2, 0),
    protoVarintField(3, 0),
  ])
  parts.push(protoMessageField(11, appState))

  return Buffer.concat(parts)
}

