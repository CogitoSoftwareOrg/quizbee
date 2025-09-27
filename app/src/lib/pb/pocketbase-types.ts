/**
* This file was @generated using pocketbase-typegen
*/

import type PocketBase from 'pocketbase'
import type { RecordService } from 'pocketbase'

export enum Collections {
	Authorigins = "_authOrigins",
	Externalauths = "_externalAuths",
	Mfas = "_mfas",
	Otps = "_otps",
	Superusers = "_superusers",
	Materials = "materials",
	Messages = "messages",
	QuizAttempts = "quizAttempts",
	QuizItems = "quizItems",
	Quizes = "quizes",
	StripeEvents = "stripeEvents",
	Subscriptions = "subscriptions",
	Users = "users",
}

// Alias types for improved usability
export type IsoDateString = string
export type RecordIdString = string
export type HTMLString = string

type ExpandType<T> = unknown extends T
	? T extends unknown
		? { expand?: unknown }
		: { expand: T }
	: { expand: T }

// System fields
export type BaseSystemFields<T = unknown> = {
	id: RecordIdString
	collectionId: string
	collectionName: Collections
} & ExpandType<T>

export type AuthSystemFields<T = unknown> = {
	email: string
	emailVisibility: boolean
	username: string
	verified: boolean
} & BaseSystemFields<T>

// Record types for each collection

export type AuthoriginsRecord = {
	collectionRef: string
	created?: IsoDateString
	fingerprint: string
	id: string
	recordRef: string
	updated?: IsoDateString
}

export type ExternalauthsRecord = {
	collectionRef: string
	created?: IsoDateString
	id: string
	provider: string
	providerId: string
	recordRef: string
	updated?: IsoDateString
}

export type MfasRecord = {
	collectionRef: string
	created?: IsoDateString
	id: string
	method: string
	recordRef: string
	updated?: IsoDateString
}

export type OtpsRecord = {
	collectionRef: string
	created?: IsoDateString
	id: string
	password: string
	recordRef: string
	sentTo?: string
	updated?: IsoDateString
}

export type SuperusersRecord = {
	created?: IsoDateString
	email: string
	emailVisibility?: boolean
	id: string
	password: string
	tokenKey: string
	updated?: IsoDateString
	verified?: boolean
}

export type MaterialsRecord = {
	created?: IsoDateString
	file?: string
	id: string
	title?: string
	updated?: IsoDateString
	user?: RecordIdString
}

export enum MessagesRoleOptions {
	"user" = "user",
	"ai" = "ai",
}

export enum MessagesStatusOptions {
	"streaming" = "streaming",
	"final" = "final",
	"onClient" = "onClient",
}
export type MessagesRecord<Tmetadata = unknown> = {
	content?: string
	created?: IsoDateString
	id: string
	metadata?: null | Tmetadata
	quizAttempt?: RecordIdString
	role?: MessagesRoleOptions
	status: MessagesStatusOptions
	tokens?: number
	updated?: IsoDateString
}

export type QuizAttemptsRecord<Tchoices = unknown, Tfeedback = unknown> = {
	choices?: null | Tchoices
	created?: IsoDateString
	feedback?: null | Tfeedback
	id: string
	quiz?: RecordIdString
	updated?: IsoDateString
	user?: RecordIdString
}

export enum QuizItemsStatusOptions {
	"final" = "final",
	"generating" = "generating",
	"blank" = "blank",
	"failed" = "failed",
	"generated" = "generated",
}
export type QuizItemsRecord<Tanswers = unknown> = {
	answers?: null | Tanswers
	created?: IsoDateString
	id: string
	order?: number
	question?: string
	quiz?: RecordIdString
	status: QuizItemsStatusOptions
	updated?: IsoDateString
}

export enum QuizesDifficultyOptions {
	"beginner" = "beginner",
	"intermediate" = "intermediate",
	"expert" = "expert",
}

export enum QuizesStatusOptions {
	"draft" = "draft",
	"creating" = "creating",
	"final" = "final",
}
export type QuizesRecord = {
	author?: RecordIdString
	created?: IsoDateString
	difficulty?: QuizesDifficultyOptions
	generation?: number
	id: string
	itemsLimit?: number
	materials?: RecordIdString[]
	query?: string
	status?: QuizesStatusOptions
	title?: string
	updated?: IsoDateString
}

export type StripeEventsRecord = {
	created?: IsoDateString
	id: string
	updated?: IsoDateString
}

export enum SubscriptionsStatusOptions {
	"active" = "active",
	"incomplete" = "incomplete",
	"trialing" = "trialing",
	"past_due" = "past_due",
	"canceled" = "canceled",
	"unpaid" = "unpaid",
}

export enum SubscriptionsTariffOptions {
	"plus" = "plus",
	"pro" = "pro",
	"free" = "free",
}
export type SubscriptionsRecord = {
	created?: IsoDateString
	currentPeriodEnd?: IsoDateString
	id: string
	messagesLimit?: number
	messagesUsage?: number
	quizItemsLimit?: number
	quizItemsUsage?: number
	status?: SubscriptionsStatusOptions
	stripeCustomer?: string
	stripeSubscription?: string
	tariff?: SubscriptionsTariffOptions
	updated?: IsoDateString
	user?: RecordIdString
}

export type UsersRecord<Tmetadata = unknown> = {
	avatar?: string
	created?: IsoDateString
	email: string
	emailVisibility?: boolean
	id: string
	metadata?: null | Tmetadata
	name?: string
	password: string
	tokenKey: string
	updated?: IsoDateString
	verified?: boolean
}

// Response types include system fields and match responses from the PocketBase API
export type AuthoriginsResponse<Texpand = unknown> = Required<AuthoriginsRecord> & BaseSystemFields<Texpand>
export type ExternalauthsResponse<Texpand = unknown> = Required<ExternalauthsRecord> & BaseSystemFields<Texpand>
export type MfasResponse<Texpand = unknown> = Required<MfasRecord> & BaseSystemFields<Texpand>
export type OtpsResponse<Texpand = unknown> = Required<OtpsRecord> & BaseSystemFields<Texpand>
export type SuperusersResponse<Texpand = unknown> = Required<SuperusersRecord> & AuthSystemFields<Texpand>
export type MaterialsResponse<Texpand = unknown> = Required<MaterialsRecord> & BaseSystemFields<Texpand>
export type MessagesResponse<Tmetadata = unknown, Texpand = unknown> = Required<MessagesRecord<Tmetadata>> & BaseSystemFields<Texpand>
export type QuizAttemptsResponse<Tchoices = unknown, Tfeedback = unknown, Texpand = unknown> = Required<QuizAttemptsRecord<Tchoices, Tfeedback>> & BaseSystemFields<Texpand>
export type QuizItemsResponse<Tanswers = unknown, Texpand = unknown> = Required<QuizItemsRecord<Tanswers>> & BaseSystemFields<Texpand>
export type QuizesResponse<Texpand = unknown> = Required<QuizesRecord> & BaseSystemFields<Texpand>
export type StripeEventsResponse<Texpand = unknown> = Required<StripeEventsRecord> & BaseSystemFields<Texpand>
export type SubscriptionsResponse<Texpand = unknown> = Required<SubscriptionsRecord> & BaseSystemFields<Texpand>
export type UsersResponse<Tmetadata = unknown, Texpand = unknown> = Required<UsersRecord<Tmetadata>> & AuthSystemFields<Texpand>

// Types containing all Records and Responses, useful for creating typing helper functions

export type CollectionRecords = {
	_authOrigins: AuthoriginsRecord
	_externalAuths: ExternalauthsRecord
	_mfas: MfasRecord
	_otps: OtpsRecord
	_superusers: SuperusersRecord
	materials: MaterialsRecord
	messages: MessagesRecord
	quizAttempts: QuizAttemptsRecord
	quizItems: QuizItemsRecord
	quizes: QuizesRecord
	stripeEvents: StripeEventsRecord
	subscriptions: SubscriptionsRecord
	users: UsersRecord
}

export type CollectionResponses = {
	_authOrigins: AuthoriginsResponse
	_externalAuths: ExternalauthsResponse
	_mfas: MfasResponse
	_otps: OtpsResponse
	_superusers: SuperusersResponse
	materials: MaterialsResponse
	messages: MessagesResponse
	quizAttempts: QuizAttemptsResponse
	quizItems: QuizItemsResponse
	quizes: QuizesResponse
	stripeEvents: StripeEventsResponse
	subscriptions: SubscriptionsResponse
	users: UsersResponse
}

// Type for usage with type asserted PocketBase instance
// https://github.com/pocketbase/js-sdk#specify-typescript-definitions

export type TypedPocketBase = PocketBase & {
	collection(idOrName: '_authOrigins'): RecordService<AuthoriginsResponse>
	collection(idOrName: '_externalAuths'): RecordService<ExternalauthsResponse>
	collection(idOrName: '_mfas'): RecordService<MfasResponse>
	collection(idOrName: '_otps'): RecordService<OtpsResponse>
	collection(idOrName: '_superusers'): RecordService<SuperusersResponse>
	collection(idOrName: 'materials'): RecordService<MaterialsResponse>
	collection(idOrName: 'messages'): RecordService<MessagesResponse>
	collection(idOrName: 'quizAttempts'): RecordService<QuizAttemptsResponse>
	collection(idOrName: 'quizItems'): RecordService<QuizItemsResponse>
	collection(idOrName: 'quizes'): RecordService<QuizesResponse>
	collection(idOrName: 'stripeEvents'): RecordService<StripeEventsResponse>
	collection(idOrName: 'subscriptions'): RecordService<SubscriptionsResponse>
	collection(idOrName: 'users'): RecordService<UsersResponse>
}
