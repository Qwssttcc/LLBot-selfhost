import { QQProtocolBase } from './base'
import { PmhqQQProtocol } from './pmhq'
import { FriendMixin, GroupMixin, MediaMixin, MessageMixin, SystemMixin, UserMixin } from './mixins'

export type {
  PBData,
  PMHQResSendPB,
  PMHQResRecvPB,
  PMHQReqSendPB,
  PMHQRes,
  PMHQReq,
  ResListener,
  QQResourceUsage,
} from './types'

export { QQProtocolBase } from './base'
export { PmhqQQProtocol } from './pmhq'


type Constructor<T = object> = abstract new (...args: any[]) => T

type Mixin<TBase extends Constructor> = (Base: TBase) => Constructor

// 从 Mixin 函数提取返回的类实例类型
type MixinInstance<T> = T extends (Base: any) => infer R
  ? R extends Constructor<infer I> ? I : never
  : never

// 递归合并 Mixin 数组的类型
type MergeMixins<TBase, TMixins extends readonly Mixin<any>[]> = TMixins extends readonly [
  infer First extends Mixin<any>,
  ...infer Rest extends readonly Mixin<any>[],
]
  ? MergeMixins<TBase & MixinInstance<First>, Rest>
  : TBase

// 带类型推导的 applyMixins. 允许具体 impl 传入 (new(...)=>QQProtocolBase); return 类型仍是抽象构造器,
// 但 InstanceType 就是完整 mixed shape.
function applyMixins<TBase extends new (...args: any[]) => object, TMixins extends readonly Mixin<any>[]>(
  Base: TBase,
  mixins: TMixins,
): new (...args: ConstructorParameters<TBase>) => MergeMixins<InstanceType<TBase>, TMixins> {
  return mixins.reduce<any>((acc, mixin) => mixin(acc), Base)
}


const mixins = [GroupMixin, FriendMixin, MediaMixin, MessageMixin, UserMixin, SystemMixin] as const

/**
 * Apply the existing protocol mixins to the external PMHQ service.
 */
export const PmhqQQProtocolClient = applyMixins(PmhqQQProtocol, mixins)

// ctx.qqProtocol 静态类型: 因为两个具体实现类都有同一套 mixin 方法, 用 InstanceType 的 union
// 会让 TS 算不出方法名交集(推 never). 直接用抽象 base + 一次性 mixin 合并类型, 结果等价于
// "任何具体 impl 都有的公共 shape". 运行期 ctx.plugin 传的还是具体 impl (含所有 mixin 方法).
type QQProtocolInstance = MergeMixins<QQProtocolBase, typeof mixins>
declare module 'cordis' {
  interface Context {
    qqProtocol: QQProtocolInstance
  }
}
