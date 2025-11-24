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
	Blog = "blog",
	BlogI18n = "blogI18n",
	Feedbacks = "feedbacks",
	Landings = "landings",
	LandingsI18n = "landingsI18n",
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
export type IsoAutoDateString = string & { readonly autodate: unique symbol }
export type RecordIdString = string
export type FileNameString = string & { readonly filename: unique symbol }
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
	created: IsoAutoDateString
	fingerprint: string
	id: string
	recordRef: string
	updated: IsoAutoDateString
}

export type ExternalauthsRecord = {
	collectionRef: string
	created: IsoAutoDateString
	id: string
	provider: string
	providerId: string
	recordRef: string
	updated: IsoAutoDateString
}

export type MfasRecord = {
	collectionRef: string
	created: IsoAutoDateString
	id: string
	method: string
	recordRef: string
	updated: IsoAutoDateString
}

export type OtpsRecord = {
	collectionRef: string
	created: IsoAutoDateString
	id: string
	password: string
	recordRef: string
	sentTo?: string
	updated: IsoAutoDateString
}

export type SuperusersRecord = {
	created: IsoAutoDateString
	email: string
	emailVisibility?: boolean
	id: string
	password: string
	tokenKey: string
	updated: IsoAutoDateString
	verified?: boolean
}

export enum BlogCategoryOptions {
	"product" = "product",
	"education" = "education",
	"edtechTrends" = "edtechTrends",
	"quizMaking" = "quizMaking",
	"useCases" = "useCases",
	"general" = "general",
}
export type BlogRecord<Ttags = unknown> = {
	category?: BlogCategoryOptions
	cover?: FileNameString
	created: IsoAutoDateString
	id: string
	published?: boolean
	slug?: string
	tags?: null | Ttags
	updated: IsoAutoDateString
}

export enum BlogI18nStatusOptions {
	"draft" = "draft",
	"published" = "published",
}

export enum BlogI18nLocaleOptions {
	"en" = "en",
	"es" = "es",
	"ru" = "ru",
	"de" = "de",
	"fr" = "fr",
	"pt" = "pt",
}
export type BlogI18nRecord<Tdata = unknown> = {
	content?: HTMLString
	created: IsoAutoDateString
	data?: null | Tdata
	id: string
	locale?: BlogI18nLocaleOptions
	post?: RecordIdString
	status?: BlogI18nStatusOptions
	updated: IsoAutoDateString
}

export enum FeedbacksTypeOptions {
	"support" = "support",
	"feature" = "feature",
}
export type FeedbacksRecord<Tmetadata = unknown> = {
	content?: string
	created: IsoAutoDateString
	id: string
	metadata?: null | Tmetadata
	rating?: number
	type?: FeedbacksTypeOptions
	updated: IsoAutoDateString
	user?: RecordIdString
}

export type LandingsRecord<Tmeta = unknown, Tstructure = unknown> = {
	created: IsoAutoDateString
	id: string
	meta?: null | Tmeta
	published?: boolean
	slug?: string
	structure?: null | Tstructure
	updated: IsoAutoDateString
	version?: number
}

export enum LandingsI18nFormatOptions {
	"plain" = "plain",
	"markdown" = "markdown",
	"html" = "html",
	"mixed" = "mixed",
}

export enum LandingsI18nStatusOptions {
	"draft" = "draft",
	"published" = "published",
}
export type LandingsI18nRecord<Tdata = unknown> = {
	created: IsoAutoDateString
	data?: null | Tdata
	format?: LandingsI18nFormatOptions
	id: string
	landing?: RecordIdString
	locale?: string
	status?: LandingsI18nStatusOptions
	updated: IsoAutoDateString
	version?: number
}

export enum MaterialsStatusOptions {
	"too big" = "too big",
	"uploaded" = "uploaded",
	"used" = "used",
	"indexing" = "indexing",
	"indexed" = "indexed",
	"deleting" = "deleting",
}

export enum MaterialsKindOptions {
	"simple" = "simple",
	"complex" = "complex",
}
export type MaterialsRecord<Tcontents = unknown> = {
	bytes?: number
	contents?: null | Tcontents
	created: IsoAutoDateString
	file?: FileNameString
	id: string
	images?: FileNameString[]
	isBook?: boolean
	kind?: MaterialsKindOptions
	status?: MaterialsStatusOptions
	textFile?: FileNameString
	title?: string
	tokens?: number
	updated: IsoAutoDateString
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
	created: IsoAutoDateString
	id: string
	metadata?: null | Tmetadata
	quizAttempt?: RecordIdString
	role?: MessagesRoleOptions
	status: MessagesStatusOptions
	tokens?: number
	updated: IsoAutoDateString
}

export type QuizAttemptsRecord<Tchoices = unknown, Tfeedback = unknown> = {
	choices?: null | Tchoices
	created: IsoAutoDateString
	feedback?: null | Tfeedback
	id: string
	quiz?: RecordIdString
	updated: IsoAutoDateString
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
	created: IsoAutoDateString
	id: string
	managed?: boolean
	order?: number
	question?: string
	quiz?: RecordIdString
	rating?: number
	status: QuizItemsStatusOptions
	updated: IsoAutoDateString
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
	"preparing" = "preparing",
	"answered" = "answered",
}

export enum QuizesVisibilityOptions {
	"private" = "private",
	"public" = "public",
	"search" = "search",
}

export enum QuizesCategoryOptions {
	"stem" = "stem",
	"general" = "general",
	"math" = "math",
	"history" = "history",
	"law" = "law",
	"language" = "language",
	"art" = "art",
	"popCulture" = "popCulture",
	"psychology" = "psychology",
}
export type QuizesRecord<TdynamicConfig = unknown, Tmetadata = unknown, Ttags = unknown> = {
	author?: RecordIdString
	avoidRepeat?: boolean
	category?: QuizesCategoryOptions
	created: IsoAutoDateString
	difficulty?: QuizesDifficultyOptions
	dynamicConfig?: null | TdynamicConfig
	generation?: number
	id: string
	itemsLimit?: number
	materials?: RecordIdString[]
	materialsContext?: FileNameString
	metadata?: null | Tmetadata
	query?: string
	slug?: string
	status?: QuizesStatusOptions
	summary?: string
	tags?: null | Ttags
	targetLanguage?: string
	title?: string
	updated: IsoAutoDateString
	visibility?: QuizesVisibilityOptions
}

export type StripeEventsRecord<Tpayload = unknown> = {
	created: IsoAutoDateString
	id: string
	payload?: null | Tpayload
	stripe?: string
	type?: string
	updated: IsoAutoDateString
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
export type SubscriptionsRecord<Tmetadata = unknown> = {
	cancelAtPeriodEnd?: boolean
	created: IsoAutoDateString
	currentPeriodEnd?: IsoDateString
	currentPeriodStart?: IsoDateString
	id: string
	metadata?: null | Tmetadata
	quizItemsLimit?: number
	quizItemsUsage?: number
	status?: SubscriptionsStatusOptions
	storageLimit?: number
	storageUsage?: number
	stripeCustomer?: string
	stripeInterval?: string
	stripePrice?: string
	stripeProduct?: string
	stripeSubscription?: string
	tariff?: SubscriptionsTariffOptions
	updated: IsoAutoDateString
	user?: RecordIdString
}

export type UsersRecord<Tmetadata = unknown> = {
	avatar?: FileNameString
	created: IsoAutoDateString
	email: string
	emailVisibility?: boolean
	id: string
	metadata?: null | Tmetadata
	name?: string
	password: string
	tokenKey: string
	updated: IsoAutoDateString
	verified?: boolean
}

// Response types include system fields and match responses from the PocketBase API
export type AuthoriginsResponse<Texpand = unknown> = Required<AuthoriginsRecord> & BaseSystemFields<Texpand>
export type ExternalauthsResponse<Texpand = unknown> = Required<ExternalauthsRecord> & BaseSystemFields<Texpand>
export type MfasResponse<Texpand = unknown> = Required<MfasRecord> & BaseSystemFields<Texpand>
export type OtpsResponse<Texpand = unknown> = Required<OtpsRecord> & BaseSystemFields<Texpand>
export type SuperusersResponse<Texpand = unknown> = Required<SuperusersRecord> & AuthSystemFields<Texpand>
export type BlogResponse<Ttags = unknown, Texpand = unknown> = Required<BlogRecord<Ttags>> & BaseSystemFields<Texpand>
export type BlogI18nResponse<Tdata = unknown, Texpand = unknown> = Required<BlogI18nRecord<Tdata>> & BaseSystemFields<Texpand>
export type FeedbacksResponse<Tmetadata = unknown, Texpand = unknown> = Required<FeedbacksRecord<Tmetadata>> & BaseSystemFields<Texpand>
export type LandingsResponse<Tmeta = unknown, Tstructure = unknown, Texpand = unknown> = Required<LandingsRecord<Tmeta, Tstructure>> & BaseSystemFields<Texpand>
export type LandingsI18nResponse<Tdata = unknown, Texpand = unknown> = Required<LandingsI18nRecord<Tdata>> & BaseSystemFields<Texpand>
export type MaterialsResponse<Tcontents = unknown, Texpand = unknown> = Required<MaterialsRecord<Tcontents>> & BaseSystemFields<Texpand>
export type MessagesResponse<Tmetadata = unknown, Texpand = unknown> = Required<MessagesRecord<Tmetadata>> & BaseSystemFields<Texpand>
export type QuizAttemptsResponse<Tchoices = unknown, Tfeedback = unknown, Texpand = unknown> = Required<QuizAttemptsRecord<Tchoices, Tfeedback>> & BaseSystemFields<Texpand>
export type QuizItemsResponse<Tanswers = unknown, Texpand = unknown> = Required<QuizItemsRecord<Tanswers>> & BaseSystemFields<Texpand>
export type QuizesResponse<TdynamicConfig = unknown, Tmetadata = unknown, Ttags = unknown, Texpand = unknown> = Required<QuizesRecord<TdynamicConfig, Tmetadata, Ttags>> & BaseSystemFields<Texpand>
export type StripeEventsResponse<Tpayload = unknown, Texpand = unknown> = Required<StripeEventsRecord<Tpayload>> & BaseSystemFields<Texpand>
export type SubscriptionsResponse<Tmetadata = unknown, Texpand = unknown> = Required<SubscriptionsRecord<Tmetadata>> & BaseSystemFields<Texpand>
export type UsersResponse<Tmetadata = unknown, Texpand = unknown> = Required<UsersRecord<Tmetadata>> & AuthSystemFields<Texpand>

// Types containing all Records and Responses, useful for creating typing helper functions

export type CollectionRecords = {
	_authOrigins: AuthoriginsRecord
	_externalAuths: ExternalauthsRecord
	_mfas: MfasRecord
	_otps: OtpsRecord
	_superusers: SuperusersRecord
	blog: BlogRecord
	blogI18n: BlogI18nRecord
	feedbacks: FeedbacksRecord
	landings: LandingsRecord
	landingsI18n: LandingsI18nRecord
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
	blog: BlogResponse
	blogI18n: BlogI18nResponse
	feedbacks: FeedbacksResponse
	landings: LandingsResponse
	landingsI18n: LandingsI18nResponse
	materials: MaterialsResponse
	messages: MessagesResponse
	quizAttempts: QuizAttemptsResponse
	quizItems: QuizItemsResponse
	quizes: QuizesResponse
	stripeEvents: StripeEventsResponse
	subscriptions: SubscriptionsResponse
	users: UsersResponse
}

// Utility types for create/update operations

type ProcessCreateAndUpdateFields<T> = Omit<{
	// Omit AutoDate fields
	[K in keyof T as Extract<T[K], IsoAutoDateString> extends never ? K : never]: 
		// Convert FileNameString to File
		T[K] extends infer U ? 
			U extends (FileNameString | FileNameString[]) ? 
				U extends any[] ? File[] : File 
			: U
		: never
}, 'id'>

// Create type for Auth collections
export type CreateAuth<T> = {
	id?: RecordIdString
	email: string
	emailVisibility?: boolean
	password: string
	passwordConfirm: string
	verified?: boolean
} & ProcessCreateAndUpdateFields<T>

// Create type for Base collections
export type CreateBase<T> = {
	id?: RecordIdString
} & ProcessCreateAndUpdateFields<T>

// Update type for Auth collections
export type UpdateAuth<T> = Partial<
	Omit<ProcessCreateAndUpdateFields<T>, keyof AuthSystemFields>
> & {
	email?: string
	emailVisibility?: boolean
	oldPassword?: string
	password?: string
	passwordConfirm?: string
	verified?: boolean
}

// Update type for Base collections
export type UpdateBase<T> = Partial<
	Omit<ProcessCreateAndUpdateFields<T>, keyof BaseSystemFields>
>

// Get the correct create type for any collection
export type Create<T extends keyof CollectionResponses> =
	CollectionResponses[T] extends AuthSystemFields
		? CreateAuth<CollectionRecords[T]>
		: CreateBase<CollectionRecords[T]>

// Get the correct update type for any collection
export type Update<T extends keyof CollectionResponses> =
	CollectionResponses[T] extends AuthSystemFields
		? UpdateAuth<CollectionRecords[T]>
		: UpdateBase<CollectionRecords[T]>

// Type for usage with type asserted PocketBase instance
// https://github.com/pocketbase/js-sdk#specify-typescript-definitions

export type TypedPocketBase = {
	collection<T extends keyof CollectionResponses>(
		idOrName: T
	): RecordService<CollectionResponses[T]>
} & PocketBase
