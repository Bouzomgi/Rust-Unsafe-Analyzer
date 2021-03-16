// Unsafe Union field call in nesting struct

fn main() {

	union Sample {
		first: u8,
		second: u8
	}

	struct Example {
		uno: Sample
	}

	struct Test {
		another : Example
	}


	let instantiation = Sample{ first: 23 };

	let new = Example{ uno: instantiation };

	let funky = Test{ another: new };

	let a = funky.another.uno.first;

}