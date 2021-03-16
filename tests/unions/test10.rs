// Unsafe Union field call as a null pointer's assignment

fn main() {

	union SomeUnion {
		first: u8
 	}

	let myUnion = SomeUnion{ first: 1 };

	unsafe {
		let myRawptr = &myUnion.first as *const u8;
	}
}
