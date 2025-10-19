/**
 * This file was @generated using pocketbase-typegen
 */

import type PocketBase from 'pocketbase';
import type { RecordService } from 'pocketbase';

export enum Collections {
	Authorigins = '_authOrigins',
	Externalauths = '_externalAuths',
	Mfas = '_mfas',
	Otps = '_otps',
	Superusers = '_superusers',
	Feedbacks = 'feedbacks',
	Blog = 'blog',
	BlogI18n = 'blogI18n',
	Feedbacks = 'feedbacks',
	Landings = 'landings',
	LandingsI18n = 'landingsI18n',
	Materials = 'materials',
	Messages = 'messages',
	QuizAttempts = 'quizAttempts',
	QuizItems = 'quizItems',
	Quizes = 'quizes',
	StripeEvents = 'stripeEvents',
	Subscriptions = 'subscriptions',
	Users = 'users'
}

// Alias types for improved usability
export type IsoDateString = string;
export type RecordIdString = string;
export type HTMLString = string;

type ExpandType<T> = unknown extends T
	? T extends unknown
		? { expand?: unknown }
		: { expand: T }
	: { expand: T };

// System fields
export type BaseSystemFields<T = unknown> = {
	id: RecordIdString;
	collectionId: string;
	collectionName: Collections;
} & ExpandType<T>;

export type AuthSystemFields<T = unknown> = {
	email: string;
	emailVisibility: boolean;
	username: string;
	verified: boolean;
} & BaseSystemFields<T>;

// Record types for each collection

export type AuthoriginsRecord = {
	collectionRef: string;
	created?: IsoDateString;
	fingerprint: string;
	id: string;
	recordRef: string;
	updated?: IsoDateString;
};

export type ExternalauthsRecord = {
	collectionRef: string;
	created?: IsoDateString;
	id: string;
	provider: string;
	providerId: string;
	recordRef: string;
	updated?: IsoDateString;
};

export type MfasRecord = {
	collectionRef: string;
	created?: IsoDateString;
	id: string;
	method: string;
	recordRef: string;
	updated?: IsoDateString;
};

export type OtpsRecord = {
	collectionRef: string;
	created?: IsoDateString;
	id: string;
	password: string;
	recordRef: string;
	sentTo?: string;
	updated?: IsoDateString;
};

export type SuperusersRecord = {
	created?: IsoDateString;
	email: string;
	emailVisibility?: boolean;
	id: string;
	password: string;
	tokenKey: string;
	updated?: IsoDateString;
	verified?: boolean;
};

export enum FeedbacksTypeOptions {
	'support' = 'support',
	'feature' = 'feature'
}
export type FeedbacksRecord<Tmetadata = unknown> = {
	content?: string;
	created?: IsoDateString;
	id: string;
	metadata?: null | Tmetadata;
	rating?: number;
	type?: FeedbacksTypeOptions;
	updated?: IsoDateString;
	user?: RecordIdString;
};

export enum BlogCategoryOptions {
	'product' = 'product',
	'education' = 'education',
	'edtechTrends' = 'edtechTrends',
	'quizMaking' = 'quizMaking',
	'useCases' = 'useCases',
	'general' = 'general'
}
export type BlogRecord<Ttags = unknown> = {
	category?: BlogCategoryOptions;
	cover?: string;
	created?: IsoDateString;
	id: string;
	published?: boolean;
	slug?: string;
	tags?: null | Ttags;
	updated?: IsoDateString;
};

export enum BlogI18nStatusOptions {
	'draft' = 'draft',
	'published' = 'published'
}

export enum BlogI18nLocaleOptions {
	'en' = 'en',
	'es' = 'es',
	'ru' = 'ru',
	'de' = 'de',
	'fr' = 'fr',
	'pt' = 'pt'
}
export type BlogI18nRecord<Tdata = unknown> = {
	content?: HTMLString;
	created?: IsoDateString;
	data?: null | Tdata;
	id: string;
	locale?: BlogI18nLocaleOptions;
	post?: RecordIdString;
	status?: BlogI18nStatusOptions;
	updated?: IsoDateString;
};

export enum FeedbacksTypeOptions {
	'support' = 'support',
	'feature' = 'feature'
}
export type FeedbacksRecord<Tmetadata = unknown> = {
	content?: string;
	created?: IsoDateString;
	id: string;
	metadata?: null | Tmetadata;
	rating?: number;
	type?: FeedbacksTypeOptions;
	updated?: IsoDateString;
	user?: RecordIdString;
};

export type LandingsRecord<Tmeta = unknown, Tstructure = unknown> = {
	created?: IsoDateString;
	id: string;
	meta?: null | Tmeta;
	published?: boolean;
	slug?: string;
	structure?: null | Tstructure;
	updated?: IsoDateString;
	version?: number;
};

export enum LandingsI18nFormatOptions {
	'plain' = 'plain',
	'markdown' = 'markdown',
	'html' = 'html',
	'mixed' = 'mixed'
}

export enum LandingsI18nStatusOptions {
	'draft' = 'draft',
	'published' = 'published'
}
export type LandingsI18nRecord<Tdata = unknown> = {
	created?: IsoDateString;
	data?: null | Tdata;
	format?: LandingsI18nFormatOptions;
	id: string;
	landing?: RecordIdString;
	locale?: string;
	status?: LandingsI18nStatusOptions;
	updated?: IsoDateString;
	version?: number;
};

export enum MaterialsStatusOptions {
	'too big' = 'too big',
	'uploaded' = 'uploaded',
	'used' = 'used'
}

export enum MaterialsKindOptions {
	'simple' = 'simple',
	'complex' = 'complex'
}
export type MaterialsRecord<Tcontents = unknown> = {
	bytes?: number;
	contents?: null | Tcontents;
	created?: IsoDateString;
	file?: string;
	id: string;
	images?: string[];
	isBook?: boolean;
	kind?: MaterialsKindOptions;
	status?: MaterialsStatusOptions;
	textFile?: string;
	title?: string;
	tokens?: number;
	updated?: IsoDateString;
	user?: RecordIdString;
};

export enum MessagesRoleOptions {
	'user' = 'user',
	'ai' = 'ai'
}

export enum MessagesStatusOptions {
	'streaming' = 'streaming',
	'final' = 'final',
	'onClient' = 'onClient'
}
export type MessagesRecord<Tmetadata = unknown> = {
	content?: string;
	created?: IsoDateString;
	id: string;
	metadata?: null | Tmetadata;
	quizAttempt?: RecordIdString;
	role?: MessagesRoleOptions;
	status: MessagesStatusOptions;
	tokens?: number;
	updated?: IsoDateString;
};

export type QuizAttemptsRecord<Tchoices = unknown, Tfeedback = unknown> = {
	choices?: null | Tchoices;
	created?: IsoDateString;
	feedback?: null | Tfeedback;
	id: string;
	quiz?: RecordIdString;
	updated?: IsoDateString;
	user?: RecordIdString;
};

export enum QuizItemsStatusOptions {
	'final' = 'final',
	'generating' = 'generating',
	'blank' = 'blank',
	'failed' = 'failed',
	'generated' = 'generated'
}
export type QuizItemsRecord<Tanswers = unknown> = {
	answers?: null | Tanswers;
	created?: IsoDateString;
	id: string;
	managed?: boolean;
	order?: number;
	question?: string;
	quiz?: RecordIdString;
	status: QuizItemsStatusOptions;
	updated?: IsoDateString;
};

export enum QuizesDifficultyOptions {
	'beginner' = 'beginner',
	'intermediate' = 'intermediate',
	'expert' = 'expert'
}

export enum QuizesStatusOptions {
	'draft' = 'draft',
	'creating' = 'creating',
	'final' = 'final',
	'preparing' = 'preparing'
}

export enum QuizesVisibilityOptions {
	'private' = 'private',
	'public' = 'public',
	'search' = 'search'
}
export type QuizesRecord<TdynamicConfig = unknown, Tmetadata = unknown, Ttags = unknown> = {
	author?: RecordIdString;
	avoidRepeat?: boolean;
	created?: IsoDateString;
	difficulty?: QuizesDifficultyOptions;
	dynamicConfig?: null | TdynamicConfig;
	generation?: number;
	id: string;
	itemsLimit?: number;
	materials?: RecordIdString[];
	materialsContext?: string;
	metadata?: null | Tmetadata;
	metadata?: null | Tmetadata;
	query?: string;
	slug?: string;
	slug?: string;
	status?: QuizesStatusOptions;
	summary?: string;
	tags?: null | Ttags;
	tags?: null | Ttags;
	title?: string;
	updated?: IsoDateString;
	visibility?: QuizesVisibilityOptions;
	visibility?: QuizesVisibilityOptions;
};

export type StripeEventsRecord<Tpayload = unknown> = {
	created?: IsoDateString;
	id: string;
	payload?: null | Tpayload;
	stripe?: string;
	type?: string;
	updated?: IsoDateString;
};

export enum SubscriptionsStatusOptions {
	'active' = 'active',
	'incomplete' = 'incomplete',
	'trialing' = 'trialing',
	'past_due' = 'past_due',
	'canceled' = 'canceled',
	'unpaid' = 'unpaid'
}

export enum SubscriptionsTariffOptions {
	'plus' = 'plus',
	'pro' = 'pro',
	'free' = 'free'
}
export type SubscriptionsRecord<Tmetadata = unknown> = {
	cancelAtPeriodEnd?: boolean;
	created?: IsoDateString;
	currentPeriodEnd?: IsoDateString;
	currentPeriodStart?: IsoDateString;
	id: string;
	lastUsageResetAt?: IsoDateString;
	messagesLimit?: number;
	messagesUsage?: number;
	metadata?: null | Tmetadata;
	quizItemsLimit?: number;
	quizItemsUsage?: number;
	quizesLimit?: number;
	quizesUsage?: number;
	status?: SubscriptionsStatusOptions;
	stripeCustomer?: string;
	stripePrice?: string;
	stripeProduct?: string;
	stripeSubscription?: string;
	tariff?: SubscriptionsTariffOptions;
	updated?: IsoDateString;
	user?: RecordIdString;
};

export type UsersRecord<Tmetadata = unknown> = {
	avatar?: string;
	created?: IsoDateString;
	email: string;
	emailVisibility?: boolean;
	id: string;
	metadata?: null | Tmetadata;
	name?: string;
	password: string;
	tokenKey: string;
	updated?: IsoDateString;
	verified?: boolean;
};

// Response types include system fields and match responses from the PocketBase API
export type AuthoriginsResponse<Texpand = unknown> = Required<AuthoriginsRecord> &
	BaseSystemFields<Texpand>;
export type ExternalauthsResponse<Texpand = unknown> = Required<ExternalauthsRecord> &
	BaseSystemFields<Texpand>;
export type MfasResponse<Texpand = unknown> = Required<MfasRecord> & BaseSystemFields<Texpand>;
export type OtpsResponse<Texpand = unknown> = Required<OtpsRecord> & BaseSystemFields<Texpand>;
export type SuperusersResponse<Texpand = unknown> = Required<SuperusersRecord> &
	AuthSystemFields<Texpand>;
export type FeedbacksResponse<Tmetadata = unknown, Texpand = unknown> = Required<
	FeedbacksRecord<Tmetadata>
> &
	BaseSystemFields<Texpand>;
export type MaterialsResponse<Tcontents = unknown, Texpand = unknown> = Required<
	MaterialsRecord<Tcontents>
> &
	BaseSystemFields<Texpand>;
export type MessagesResponse<Tmetadata = unknown, Texpand = unknown> = Required<
	MessagesRecord<Tmetadata>
> &
	BaseSystemFields<Texpand>;
export type QuizAttemptsResponse<
	Tchoices = unknown,
	Tfeedback = unknown,
	Texpand = unknown
> = Required<QuizAttemptsRecord<Tchoices, Tfeedback>> & BaseSystemFields<Texpand>;
export type QuizItemsResponse<Tanswers = unknown, Texpand = unknown> = Required<
	QuizItemsRecord<Tanswers>
> &
	BaseSystemFields<Texpand>;
export type QuizesResponse<
	TdynamicConfig = unknown,
	Tmetadata = unknown,
	Ttags = unknown,
	Texpand = unknown
> = Required<QuizesRecord<TdynamicConfig, Tmetadata, Ttags>> & BaseSystemFields<Texpand>;
export type QuizesResponse<
	TdynamicConfig = unknown,
	Tmetadata = unknown,
	Ttags = unknown,
	Texpand = unknown
> = Required<QuizesRecord<TdynamicConfig, Tmetadata, Ttags>> & BaseSystemFields<Texpand>;
export type StripeEventsResponse<Tpayload = unknown, Texpand = unknown> = Required<
	StripeEventsRecord<Tpayload>
> &
	BaseSystemFields<Texpand>;
export type SubscriptionsResponse<Tmetadata = unknown, Texpand = unknown> = Required<
	SubscriptionsRecord<Tmetadata>
> &
	BaseSystemFields<Texpand>;
export type UsersResponse<Tmetadata = unknown, Texpand = unknown> = Required<
	UsersRecord<Tmetadata>
> &
	AuthSystemFields<Texpand>;

// Types containing all Records and Responses, useful for creating typing helper functions

export type CollectionRecords = {
	_authOrigins: AuthoriginsRecord;
	_externalAuths: ExternalauthsRecord;
	_mfas: MfasRecord;
	_otps: OtpsRecord;
	_superusers: SuperusersRecord;
	feedbacks: FeedbacksRecord;
	materials: MaterialsRecord;
	messages: MessagesRecord;
	quizAttempts: QuizAttemptsRecord;
	quizItems: QuizItemsRecord;
	quizes: QuizesRecord;
	stripeEvents: StripeEventsRecord;
	subscriptions: SubscriptionsRecord;
	users: UsersRecord;
};

export type CollectionResponses = {
	_authOrigins: AuthoriginsResponse;
	_externalAuths: ExternalauthsResponse;
	_mfas: MfasResponse;
	_otps: OtpsResponse;
	_superusers: SuperusersResponse;
	feedbacks: FeedbacksResponse;
	materials: MaterialsResponse;
	messages: MessagesResponse;
	quizAttempts: QuizAttemptsResponse;
	quizItems: QuizItemsResponse;
	quizes: QuizesResponse;
	stripeEvents: StripeEventsResponse;
	subscriptions: SubscriptionsResponse;
	users: UsersResponse;
};

// Type for usage with type asserted PocketBase instance
// https://github.com/pocketbase/js-sdk#specify-typescript-definitions

export type TypedPocketBase = PocketBase & {
	collection(idOrName: '_authOrigins'): RecordService<AuthoriginsResponse>;
	collection(idOrName: '_externalAuths'): RecordService<ExternalauthsResponse>;
	collection(idOrName: '_mfas'): RecordService<MfasResponse>;
	collection(idOrName: '_otps'): RecordService<OtpsResponse>;
	collection(idOrName: '_superusers'): RecordService<SuperusersResponse>;
	collection(idOrName: 'feedbacks'): RecordService<FeedbacksResponse>;
	collection(idOrName: 'materials'): RecordService<MaterialsResponse>;
	collection(idOrName: 'messages'): RecordService<MessagesResponse>;
	collection(idOrName: 'quizAttempts'): RecordService<QuizAttemptsResponse>;
	collection(idOrName: 'quizItems'): RecordService<QuizItemsResponse>;
	collection(idOrName: 'quizes'): RecordService<QuizesResponse>;
	collection(idOrName: 'stripeEvents'): RecordService<StripeEventsResponse>;
	collection(idOrName: 'subscriptions'): RecordService<SubscriptionsResponse>;
	collection(idOrName: 'users'): RecordService<UsersResponse>;
};
