// Unsafe Union field call as a parameter to a function

fn main() {

	union SomeUnion {
		first: u8
 	}

	let myUnion = SomeUnion{ first: 23 };

	unsafe { mirrorValue(myUnion.first); }
}

fn mirrorValue(a: u8) -> u8 {
	return a
}
