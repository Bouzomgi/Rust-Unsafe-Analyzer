// Standard declared union field access

fn main() {

	union SomeUnion { 
		first: u8 
	}

	let myUnion = SomeUnion{ first: 1 };

	unsafe { let a = myUnion.first; }
}


