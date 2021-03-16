// Unsafe Union field call in struct

fn main() {

	union Sample {
		first: u8,
		second: u8
	}

	let instantiation = Sample{ first: 23 };

	let a = instantiation.first;

	struct Example {
		uno: Sample
	}

	let new = Example{ uno: instantiation };

	let a = new.uno.first;

}