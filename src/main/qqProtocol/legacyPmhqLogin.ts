/** Explicit PMHQ 7 login compatibility. Uses the backend's real RPC/results, never platform registration. */
export type LegacyCall = (func: 'getSelfInfo' | 'loginService.getQRCodePicture', args: unknown[], timeout: number) => Promise<unknown>
export type LegacySubscribe = (listener: (event: any) => void) => () => void
export interface LegacyQr { pngBase64QrcodeData: string; qrcodeUrl: string; expireTime: number; pollTimeInterval: number }
export function usesLegacyPmhq(argv = process.argv): boolean { return argv.includes('--pmhq-legacy') }
export class LegacyPmhqLogin {
  constructor(private call: LegacyCall, private subscribe: LegacySubscribe, private timeout = 8000) {}
  async readSelfInfo(): Promise<{ uin?: string; uid?: string; nick?: string }> {
    const info = await this.call('getSelfInfo', [], this.timeout)
    if (!info || typeof info !== 'object' || typeof (info as any).online !== 'boolean') throw new Error('Legacy PMHQ returned invalid login status')
    const d = info as any
    if (!d.online) return {}
    const uin = String(d.uin ?? '')
    if (!/^[1-9]\d*$/.test(uin) || typeof d.uid !== 'string' || !d.uid) throw new Error('Legacy PMHQ online identity is incomplete')
    return { uin, uid: d.uid, nick: typeof d.nick === 'string' ? d.nick : undefined }
  }
  fetchQr(): Promise<LegacyQr> {
    return new Promise((resolve, reject) => {
      let done = false
      let accepted = false
      let qr: LegacyQr | undefined
      let unsubscribe: () => void = () => {}
      const finish = (error?: Error) => {
        if (done || (!error && (!accepted || !qr))) return
        done = true
        clearTimeout(timer)
        unsubscribe()
        if (error) reject(error)
        else resolve(qr!)
      }
      const timer = setTimeout(() => finish(new Error('Legacy PMHQ QR callback timeout')), this.timeout)
      unsubscribe = this.subscribe(event => {
        if (event?.type !== 'nodeIKernelLoginListener' || event?.data?.sub_type !== 'onQRCodeGetPicture') return
        const d = event.data.data
        if (!d || typeof d.qrcodeUrl !== 'string' || !d.qrcodeUrl || typeof d.pngBase64QrcodeData !== 'string' || !d.pngBase64QrcodeData || typeof d.expireTime !== 'number' || !Number.isFinite(d.expireTime) || d.expireTime <= 0) return
        qr = { pngBase64QrcodeData: d.pngBase64QrcodeData, qrcodeUrl: d.qrcodeUrl, expireTime: d.expireTime, pollTimeInterval: typeof d.pollTimeInterval === 'number' && d.pollTimeInterval > 0 ? d.pollTimeInterval : 3 }
        finish()
      })
      this.call('loginService.getQRCodePicture', [], this.timeout).then(result => {
        if (result && typeof result === 'object' && Object.hasOwn(result, 'result') && Number((result as any).result) !== 0) {
          finish(new Error('Legacy PMHQ QR request was rejected'))
          return
        }
        accepted = true
        finish()
      }, () => finish(new Error('Legacy PMHQ QR request failed')))
    })
  }
}
