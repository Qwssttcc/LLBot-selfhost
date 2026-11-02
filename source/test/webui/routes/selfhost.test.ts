import { describe, it, expect, vi } from 'vitest'
import { Hono } from 'hono'
import { authMiddleware } from '@/webui/BE/auth'
import { hashPassword } from '@/webui/BE/passwordHash'
import { createLoginRoutes } from '@/webui/BE/routes/login'
import { selfInfo } from '@/common/globalVars'
function app(connected: boolean) {
  const api = new Hono()
  api.use('/api/*', (c,next) => { c.env = { incoming: { socket: {remoteAddress:'127.0.0.1'} } }; return authMiddleware(c,next) })
  api.route('/api',createLoginRoutes({qqProtocol:{get_is_connected:()=>connected}} as any))
  return api
}
describe('selfhost backend status and access boundary',()=>{
  it('requires the local WebUI password',async()=>{
    expect((await app(false).request('/api/backend-status')).status).toBe(403)
  })
  it('reports a disconnected offline backend honestly',async()=>{
    selfInfo.online=false
    const res=await app(false).request('/api/backend-status',{headers:{'x-webui-token':hashPassword('test-token')}})
    expect(res.status).toBe(200)
    expect((await res.json()).data).toEqual({mode:'external-pmhq',connected:false,online:false})
  })
  it('does not equate a transport connection with successful QQ login',async()=>{
    selfInfo.online=false
    const res=await app(true).request('/api/backend-status',{headers:{'x-webui-token':hashPassword('test-token')}})
    expect((await res.json()).data).toEqual({mode:'external-pmhq',connected:true,online:false})
  })
  it.each(['GET','POST'])('has no provider credential endpoint (%s)',async method=>{
    const res=await app(false).request('/api/auth-token'+(method==='GET'?'/status':''),{method,headers:{'x-webui-token':hashPassword('test-token')}})
    expect(res.status).toBe(404)
  })
})
