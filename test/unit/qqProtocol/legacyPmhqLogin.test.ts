import {afterEach,describe,it,expect,vi} from 'vitest'
import {LegacyPmhqLogin,usesLegacyPmhq} from '@/main/qqProtocol/legacyPmhqLogin'
const qr={pngBase64QrcodeData:'test-image',qrcodeUrl:'test-qr',expireTime:120,pollTimeInterval:3}
const event=(data:any=qr)=>({type:'nodeIKernelLoginListener',data:{sub_type:'onQRCodeGetPicture',data}})
function fixture(call=vi.fn().mockResolvedValue({result:0})){
 const listeners=new Set<(e:any)=>void>();const remove=vi.fn()
 const login=new LegacyPmhqLogin(call,f=>{listeners.add(f);return()=>{listeners.delete(f);remove()}},100)
 return {login,call,listeners,remove,emit:(e:any)=>{for(const f of listeners)f(e)}}
}
afterEach(()=>{vi.useRealTimers();vi.restoreAllMocks()})
describe('explicit PMHQ 7 login compatibility',()=>{
 it('does not silently select legacy mode',()=>{expect(usesLegacyPmhq([])).toBe(false);expect(usesLegacyPmhq(['--pmhq-legacy'])).toBe(true)})
 it('preserves offline status even when stale identity fields exist',async()=>{const f=fixture(vi.fn().mockResolvedValue({online:false,uin:'123',uid:'stale'}));expect(await f.login.readSelfInfo()).toEqual({})})
 it('uses the actual online identity',async()=>{const f=fixture(vi.fn().mockResolvedValue({online:true,uin:123,uid:'test-uid',nick:'test'}));expect(await f.login.readSelfInfo()).toEqual({uin:'123',uid:'test-uid',nick:'test'});expect(f.call).toHaveBeenCalledWith('getSelfInfo',[],100)})
 it.each([null,{}, {online:'true'}, {online:true,uin:'123'}, {online:true,uin:'0',uid:'test'}, {online:true,uin:'bad',uid:'test'}])('rejects an invalid identity instead of marking online: %s',async info=>{const f=fixture(vi.fn().mockResolvedValue(info));await expect(f.login.readSelfInfo()).rejects.toThrow()})
 it('handles a callback arriving before the RPC acknowledgement',async()=>{let accept!:(x:any)=>void;const f=fixture(vi.fn().mockImplementation(()=>new Promise(r=>accept=r)));const p=f.login.fetchQr();f.emit(event());expect(f.remove).not.toHaveBeenCalled();accept({result:0});await expect(p).resolves.toEqual(qr);expect(f.remove).toHaveBeenCalledTimes(1)})
 it('handles a callback arriving after acknowledgement',async()=>{const f=fixture();const p=f.login.fetchQr();await Promise.resolve();f.emit(event());await expect(p).resolves.toEqual(qr);expect(f.listeners.size).toBe(0)})
 it('ignores unrelated and malformed callbacks until a genuine QR arrives',async()=>{const f=fixture();const p=f.login.fetchQr();f.emit({type:'recv',data:{}});f.emit(event({...qr,expireTime:0}));f.emit(event({...qr,pngBase64QrcodeData:''}));f.emit(event());await expect(p).resolves.toEqual(qr)})
 it('does not accept a callback for a rejected request',async()=>{const f=fixture(vi.fn().mockResolvedValue({result:1}));const p=f.login.fetchQr();f.emit(event());await expect(p).rejects.toThrow('rejected');expect(f.listeners.size).toBe(0)})
 it('cleans up on RPC failure',async()=>{const f=fixture(vi.fn().mockRejectedValue(new Error('unavailable')));await expect(f.login.fetchQr()).rejects.toThrow('failed');expect(f.listeners.size).toBe(0)})
 it('has a bounded callback wait and removes its listener',async()=>{vi.useFakeTimers();const f=fixture();const p=f.login.fetchQr();const result=expect(p).rejects.toThrow('timeout');await vi.advanceTimersByTimeAsync(101);await result;expect(f.listeners.size).toBe(0)})
})
