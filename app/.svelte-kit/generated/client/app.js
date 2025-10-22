import * as client_hooks from '../../../src/hooks.client.ts';


export { matchers } from './matchers.js';

export const nodes = [
	() => import('./nodes/0'),
	() => import('./nodes/1'),
	() => import('./nodes/2'),
	() => import('./nodes/3'),
	() => import('./nodes/4'),
	() => import('./nodes/5'),
	() => import('./nodes/6'),
	() => import('./nodes/7'),
	() => import('./nodes/8'),
	() => import('./nodes/9'),
	() => import('./nodes/10'),
	() => import('./nodes/11'),
	() => import('./nodes/12'),
	() => import('./nodes/13'),
	() => import('./nodes/14'),
	() => import('./nodes/15')
];

export const server_loads = [];

export const dictionary = {
		"/(user)": [6,[2]],
		"/(user)/analytics": [7,[2]],
		"/(user)/attempts": [8,[2]],
		"/(user)/home": [9,[2]],
		"/(user)/profile": [10,[2]],
		"/(user)/quizes": [11,[2]],
		"/(user)/quizes/new": [15,[2]],
		"/(user)/quizes/[quizId]": [12,[2,3]],
		"/(user)/quizes/[quizId]/attempts/[quizAttemptId]": [13,[2,3]],
		"/(user)/quizes/[quizId]/attempts/[quizAttemptId]/feedback": [14,[2,3]],
		"/(auth)/sign-in": [4],
		"/(auth)/sign-up": [5]
	};

export const hooks = {
	handleError: client_hooks.handleError || (({ error }) => { console.error(error) }),
	init: client_hooks.init,
	reroute: (() => {}),
	transport: {}
};

export const decoders = Object.fromEntries(Object.entries(hooks.transport).map(([k, v]) => [k, v.decode]));

export const hash = false;

export const decode = (type, value) => decoders[type](value);

export { default as root } from '../root.js';