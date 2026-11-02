import { describe, it, expect, vi } from 'vitest'
vi.unmock('@/common/utils/environment')
import { getPmhqTarget, isPmhqMode } from '@/common/utils/environment'
const argv = (...args: string[]) => ['node', 'main.ts', ...args]
describe('external-PMHQ-only target', () => {
  it('defaults to local PMHQ rather than native signing', () => {
    expect(getPmhqTarget(argv())).toEqual({host:'127.0.0.1',port:'13000'})
    expect(getPmhqTarget(argv('--pmhq-host=pmhq'))).toEqual({host:'pmhq',port:'13000'})
    expect(isPmhqMode()).toBe(true)
  })
  it.each([
    ['--pmhq-port','13001','--pmhq-host','pmhq'],
    ['--pmhq-port=13001','--pmhq-host=pmhq'],
  ])('accepts explicit host and port: %s', (...args) => {
    expect(getPmhqTarget(argv(...args))).toEqual({host:'pmhq',port:'13001'})
  })
  it.each(['0','65536','-1','abc','13000/path',''])('rejects invalid ports: %s', port => {
    expect(() => getPmhqTarget(argv('--pmhq-port='+port))).toThrow()
  })
  it.each(['','http://pmhq','host/path','name@host','a b'])('rejects invalid hosts: %s', host => {
    expect(() => getPmhqTarget(argv('--pmhq-host='+host))).toThrow()
  })
  it('rejects missing arguments instead of choosing another backend', () => {
    expect(() => getPmhqTarget(argv('--pmhq-port','--dev'))).toThrow()
    expect(() => getPmhqTarget(argv('--pmhq-host'))).toThrow()
  })
  it('legacy Direct flags cannot enable Direct mode', () => {
    expect(getPmhqTarget(argv('--dev','--cdn=china'))).toEqual({host:'127.0.0.1',port:'13000'})
    expect(isPmhqMode()).toBe(true)
  })
})
