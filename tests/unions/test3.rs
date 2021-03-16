// Standard function safe union field call

unsafe fn main() {

	union Sample {
		first: u8,
		second: u8
	}

	let instantiation = Sample{ first: 23 };

	let a = instantiation.first;

}